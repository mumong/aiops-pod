"""
全局场景检测器节点

职责：
- 并行运行多个场景检测器
- 检测所有可能的异常场景
- 输出多场景判定结果

设计原则：
- 高内聚：检测逻辑独立，不依赖其他节点
- 低耦合：通过输入/输出接口交互
"""

import logging
import time
from typing import List, Dict, Any, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.state import WorkflowState
from app.core.workflow.multi_scenario.output import ScenarioDecision, MultiScenarioOutput
from app.core.skills.models import Layer, EvidenceLevel
from app.core.skills.engine import RulesEngine, get_engine
from app.core.skills.evidence import EvidenceExtractor

logger = logging.getLogger(__name__)


class ScenarioDetector:
    """
    场景检测器基类

    每个检测器负责检测特定类型的场景
    """

    def __init__(self, scenario_id: str, scenario_name: str, layer: Layer):
        self.scenario_id = scenario_id
        self.scenario_name = scenario_name
        self.layer = layer

    def detect(self, question: str, tool_results: List[Dict]) -> ScenarioDecision:
        """
        检测场景

        Args:
            question: 用户问题
            tool_results: 工具调用结果列表

        Returns:
            ScenarioDecision 对象
        """
        raise NotImplementedError("Subclasses must implement detect()")


class EvidenceBasedDetector(ScenarioDetector):
    """
    基于证据的检测器

    使用规则引擎和证据提取器进行检测
    """

    def __init__(self, scenario_id: str, scenario_name: str, layer: Layer):
        super().__init__(scenario_id, scenario_name, layer)
        self.engine = get_engine()

    def detect(self, question: str, tool_results: List[Dict]) -> ScenarioDecision:
        """
        使用规则引擎检测场景
        """
        # 合并所有工具输出为文本
        tool_text = ""
        for result in tool_results:
            if "result" in result:
                tool_text += str(result["result"]) + "\n"

        # 使用规则引擎评估
        decision = self.engine.evaluate(question, tool_text)

        if decision:
            # 转换为 ScenarioDecision
            return self._convert_to_scenario_decision(decision, tool_results)

        # 如果规则引擎未命中，返回空判定
        return self._create_empty_decision(question)

    def _convert_to_scenario_decision(
        self,
        decision: Any,
        tool_results: List[Dict]
    ) -> ScenarioDecision:
        """转换规则引擎决策为场景决策"""
        from app.core.skills.models import Confidence, ScenarioSeverity

        # 确定严重程度（基于层级和置信度）
        severity = self._determine_severity(decision.layer, decision.confidence_score)

        # 收集受影响的实体
        affected_entities = self._extract_affected_entities(decision, tool_results)

        # 收集证据
        collected_evidence = []
        missing_evidence = []
        for item in decision.evidence_details:
            if item.get("collected"):
                collected_evidence.append(item["description"])
            else:
                missing_evidence.append(item["description"])

        return ScenarioDecision(
            scenario_id=self.scenario_id,
            scenario_name=self.scenario_name,
            layer=decision.layer,
            severity=severity,
            confidence=decision.confidence,
            confidence_score=decision.confidence_score,
            evidence_count=len(decision.evidence_details),
            evidence_total=len(decision.evidence_details),
            collected_evidence=collected_evidence,
            missing_evidence=missing_evidence,
            issue_summary=decision.issue_summary,
            detailed_description=decision.get("issue_summary", ""),
            root_cause=decision.causal_chain.get("root_cause", ""),
            causal_chain=decision.causal_chain,
            remediation_steps=decision.remediation_steps,
            verification_steps=decision.verification_steps,
            source_tools=self._extract_source_tools(tool_results),
            referenced_evidence=collected_evidence,
            affected_entities=affected_entities,
            related_scenarios=[]
        )

    def _determine_severity(self, layer: Layer, confidence_score: float):
        """根据层级和置信度确定严重程度"""
        from app.core.skills.models import ScenarioSeverity, Confidence

        # L0/L1 层级问题通常更严重
        if layer in (Layer.L0, Layer.L1):
            if confidence_score >= 0.7:
                return ScenarioSeverity.CRITICAL
            return ScenarioSeverity.HIGH

        # L2/L3/L4 层级
        if confidence_score >= 0.8:
            return ScenarioSeverity.HIGH
        elif confidence_score >= 0.5:
            return ScenarioSeverity.MEDIUM
        else:
            return ScenarioSeverity.LOW

    def _extract_affected_entities(self, decision: Any, tool_results: List[Dict]) -> Dict[str, Any]:
        """提取受影响的实体"""
        entities = {}

        # 从决策上下文中提取
        if hasattr(decision, "context") and decision.context:
            for key, value in decision.context.items():
                if value and value != "<未知>":
                    entities[key] = value

        return entities

    def _extract_source_tools(self, tool_results: List[Dict]) -> List[str]:
        """提取使用的工具"""
        tools = []
        for result in tool_results:
            if "tool_name" in result:
                tools.append(result["tool_name"])
        return list(set(tools))

    def _create_empty_decision(self, question: str) -> ScenarioDecision:
        """创建空判定（未检测到场景）"""
        from app.core.skills.models import ScenarioSeverity, Confidence

        return ScenarioDecision(
            scenario_id=self.scenario_id,
            scenario_name=self.scenario_name,
            layer=self.layer,
            severity=ScenarioSeverity.LOW,
            confidence=Confidence.LOW,
            confidence_score=0.0,
            evidence_count=0,
            evidence_total=0,
            collected_evidence=[],
            missing_evidence=[],
            issue_summary=f"未检测到 {self.scenario_name} 场景",
            detailed_description=f"在问题 '{question[:50]}...' 中未找到 {self.scenario_name} 相关证据",
            root_cause="",
            causal_chain={},
            remediation_steps=[],
            verification_steps=[],
            source_tools=[],
            referenced_evidence=[],
            affected_entities={},
            related_scenarios=[]
        )


class GlobalDetectorNode(WorkflowNode):
    """
    全局场景检测器节点

    并行运行多个场景检测器，检测所有可能的异常场景
    """

    def __init__(self, holmes_service: Any = None, detectors: List[ScenarioDetector] = None):
        super().__init__()

        self.holmes_service = holmes_service
        self.detectors = detectors or self._get_default_detectors()

    def _get_default_detectors(self) -> List[ScenarioDetector]:
        """获取默认检测器列表"""
        from app.core.skills.models import Layer, EvidenceLevel
        # 并发检测场景
        return [
            EvidenceBasedDetector("L0-DiskFull", "磁盘空间不足", Layer.L0),
            EvidenceBasedDetector("L1-KubeletCert", "Kubelet 证书异常", Layer.L1),
            EvidenceBasedDetector("L2-OOMKilled", "内存超限被终止", Layer.L2),
            EvidenceBasedDetector("L2-VolumeLimitExceeded", "存储卷超限", Layer.L2),
            EvidenceBasedDetector("L3-DNSLatency", "DNS 解析延迟", Layer.L3),
            EvidenceBasedDetector("L3-NetworkConnectivity", "网络连通性", Layer.L3),
            EvidenceBasedDetector("L4-Dependency503", "依赖服务异常", Layer.L4),
            EvidenceBasedDetector("L4-ImagePullFailed", "镜像拉取失败", Layer.L4),
        ]

    @property
    def node_id(self) -> str:
        return "global_detector"

    @property
    def node_name(self) -> str:
        return "全局场景检测"

    def get_required_fields(self) -> List[str]:
        return ["question"]

    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        执行全局场景检测

        流程：
        1. 从状态中提取工具调用结果
        2. 并行运行所有检测器
        3. 聚合所有检测到的场景
        """
        new_state: WorkflowState = {
            "current_node": self.node_id,
        }

        try:
            question = state.get("question", "")
            start_time = time.time()

            logger.info(f"🔍 全局场景检测开始: {len(self.detectors)} 个检测器")

            # 获取工具调用结果（从状态中）
            tool_results = self._extract_tool_results(state)

            # 并行运行所有检测器
            all_decisions = self._run_detectors_parallel(question, tool_results)

            # 过滤有效的判定（置信度 > 0）
            valid_decisions = [
                d for d in all_decisions if d.confidence_score > 0.1
            ]

            logger.info(f"✅ 检测完成: 发现 {len(valid_decisions)} 个异常场景")

            # 构建多场景输出
            multi_output = MultiScenarioOutput()
            for decision in valid_decisions:
                multi_output.add_scenario(decision)

            # 存储结果到状态
            new_state.update({
                "multi_scenario_decisions": multi_output,
                "detected_scenarios": [d.to_dict() for d in valid_decisions],
                "detection_duration": time.time() - start_time,
            })

        except Exception as e:
            logger.error(f"❌ 全局场景检测失败: {e}", exc_info=True)
            new_state.setdefault("errors", []).append(
                f"节点 {self.node_id} 执行失败: {str(e)}"
            )

        return new_state

    def _extract_tool_results(self, state: WorkflowState) -> List[Dict]:
        """从状态中提取工具调用结果"""
        # 尝试从多个可能的字段中获取
        tool_results = []

        # 从 evidence_items 中提取
        evidence_items = state.get("evidence_items", [])
        for item in evidence_items:
            if hasattr(item, 'value') and item.value:
                tool_results.append({
                    "tool": "evidence_extraction",
                    "result": str(item.value)
                })

        # 从 tool_results 字段提取（如果有）
        if "tool_results" in state:
            tool_results.extend(state["tool_results"])

        return tool_results

    def _run_detectors_parallel(
        self,
        question: str,
        tool_results: List[Dict]
    ) -> List[ScenarioDecision]:
        """
        并行运行所有检测器

        Args:
            question: 用户问题
            tool_results: 工具调用结果

        Returns:
            所有检测器的判定结果列表
        """
        decisions = []

        # 使用线程池并行运行
        max_workers = min(len(self.detectors), 4)  # 最多4个并发

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_detector = {
                executor.submit(detector.detect, question, tool_results): detector
                for detector in self.detectors
            }

            # 等待所有检测完成
            for future in as_completed(future_to_detector):
                try:
                    detector = future_to_detector[future]
                    decision = detector.detect(question, tool_results)
                    if decision:
                        decisions.append(decision)
                        logger.debug(f"✅ {detector.scenario_id}: 置信度 {decision.confidence_score:.2f}")
                except Exception as e:
                    logger.error(f"❌ 检测器失败: {e}")

        return decisions
