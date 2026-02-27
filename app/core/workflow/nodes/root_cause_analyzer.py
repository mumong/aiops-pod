"""
节点3：根因分析

职责：
- 调用 LLM 基于证据进行根因推理
- 构建因果链
- 输出：root_cause, causal_chain, rca_analysis

设计：
- 有自己的专用 prompt
- 调用 LLM 进行独立分析（使用和 HolmesService 相同的方式）
- 支持使用 runbooks 和 tools
- 结合规则引擎验证结论
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.state import WorkflowState
from app.core.skills.models import (
    Layer, DeterministicDecision, EvidenceItem,
    EvidenceLevel, Confidence
)
from app.core.skills.engine import get_engine
from app.core.skills.gate import apply_gate
from app.core.prompts import get_workflow_prompt
from holmes.core.prompt import build_initial_ask_messages

logger = logging.getLogger(__name__)


class RootCauseAnalyzerNode(WorkflowNode):
    """
    根因分析节点

    每次执行都会调用 LLM 进行根因推理
    """

    def __init__(self, holmes_service: Any = None, metrics: Any = None, runbook_catalog: Any = None):
        """
        初始化节点

        Args:
            holmes_service: HolmesService 实例（用于 LLM 调用）
            metrics: WorkflowMetrics 实例（用于记录统计）
            runbook_catalog: RunbookCatalog 实例（用于 runbook 匹配）
        """
        self.holmes_service = holmes_service
        self.metrics = metrics
        self.runbook_catalog = runbook_catalog
        self.engine = get_engine()
    
    @property
    def node_id(self) -> str:
        return "rca"
    
    @property
    def node_name(self) -> str:
        return "根因分析"
    
    def get_required_fields(self) -> List[str]:
        return ["question", "layer", "evidence_items"]
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        执行根因分析逻辑
        
        1. 整理证据摘要
        2. 调用 LLM 进行根因推理
        3. 可选：用规则引擎验证
        """
        new_state: WorkflowState = {
            "current_node": self.node_id,
        }
        
        try:
            question = state.get("question", "")
            layer = state.get("layer")
            evidence_items = state.get("evidence_items", [])
            evidence_analysis = state.get("evidence_analysis", "{}")
            
            logger.info(f"🔍 根因分析: 层级={layer}, 证据数量={len(evidence_items)}")
            
            # 构建证据摘要
            evidence_summary = self._build_evidence_summary(evidence_items)
            
            # 使用 LLM 分析
            if self.holmes_service and self.holmes_service.ai:
                rca_result = self._analyze_with_llm(
                    question, layer, evidence_summary
                )
            else:
                # 回退到规则引擎
                logger.info("⚠️ 无 LLM 服务，使用规则引擎")
                rca_result = self._analyze_with_rules(
                    question, layer, evidence_items
                )
            
            # 构建决策对象
            decision = self._build_decision(layer, evidence_items, rca_result)
            
            rca_analysis_text = json.dumps(rca_result, ensure_ascii=False)

            new_state.update({
                "deterministic_decision": decision,
                "root_cause": rca_result.get("root_cause", ""),
                "causal_chain": rca_result.get("causal_chain", {}),
                "rca_analysis": rca_analysis_text,
            })

            # 同步写入通用节点分析视图
            node_analyses = new_state.get("node_analyses") or {}
            node_analyses[self.node_id] = rca_analysis_text
            new_state["node_analyses"] = node_analyses
            
            logger.info(f"✅ 根因分析完成: {rca_result.get('root_cause', '')[:50]}...")
        
        except Exception as e:
            logger.error(f"根因分析失败: {e}", exc_info=True)
            new_state.setdefault("errors", []).append(
                f"节点 {self.node_id} 执行失败: {str(e)}"
            )
            new_state.update({
                "deterministic_decision": None,
                "root_cause": f"根因分析失败: {str(e)}",
                "causal_chain": {},
                "rca_analysis": "{}",
            })
        
        return new_state
    
    def _build_evidence_summary(self, evidence_items: List[EvidenceItem]) -> str:
        """构建证据摘要"""
        lines = []
        for i, item in enumerate(evidence_items, 1):
            status = "✅ 已采集" if item.collected else "❌ 未采集"
            value = f"= {item.value}" if item.value else ""
            lines.append(f"{i}. [{status}] {item.description} {value}")
        return "\n".join(lines) if lines else "暂无证据"
    
    def _analyze_with_llm(
        self,
        question: str,
        layer: Optional[Layer],
        evidence_summary: str
    ) -> Dict:
        """使用 LLM 进行根因分析（使用和 HolmesService 相同的方式）"""
        import time

        try:
            layer_str = layer.value if layer else "L2"

            start_time = time.time()

            # 构建 system prompt
            base_prompt = get_workflow_prompt(self.node_id)
            system_prompt = base_prompt.format(
                layer=layer_str,
                evidence_summary=evidence_summary
            )

            # 使用 build_initial_ask_messages 构建消息
            # 这样可以支持 runbooks 和 tools
            messages = build_initial_ask_messages(
                console=self.holmes_service.console,
                initial_user_prompt=question,
                file_paths=None,
                tool_executor=self.holmes_service.ai.tool_executor,
                runbooks=self.runbook_catalog,
                system_prompt_additions=system_prompt
            )

            # 调用 LLM（使用和 HolmesService 相同的方式，注入 prompt）
            if self.holmes_service.stream_output:
                response = self.holmes_service._call_with_stream(messages)
            else:
                response = self.holmes_service.ai.call(messages)

            llm_duration_ms = (time.time() - start_time) * 1000

            # 记录 LLM 调用
            if self.metrics:
                self.metrics.record_llm_call("rca", llm_duration_ms)

            logger.debug(f"LLM 根因分析完成 (耗时 {llm_duration_ms:.0f}ms)")

            if response and response.result:
                return self._parse_llm_response(response.result)

            return self._analyze_with_rules(question, layer, [])

        except Exception as e:
            logger.warning(f"LLM 分析失败，回退到规则: {e}")
            return self._analyze_with_rules(question, layer, [])
    
    def _parse_llm_response(self, response_text: str) -> Dict:
        """解析 LLM 的 JSON 响应"""
        try:
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            return json.loads(response_text)
        except json.JSONDecodeError:
            # 从文本中提取关键信息
            return {
                "phenomenon": "",
                "evidence_analysis": [],
                "causal_chain": {
                    "trigger": "待分析",
                    "mechanism": "待分析",
                    "manifestation": "待分析"
                },
                "root_cause": response_text[:300],
                "confidence": 0.5,
                "confidence_reason": "LLM 输出解析失败",
                "alternative_causes": []
            }
    
    def _analyze_with_rules(
        self,
        question: str,
        layer: Optional[Layer],
        evidence_items: List[EvidenceItem]
    ) -> Dict:
        """使用规则引擎分析（回退方案）"""
        evidence_text = self._build_evidence_summary(evidence_items)
        combined_text = f"{question}\n{evidence_text}"
        
        # 尝试规则引擎
        decision = self.engine.evaluate(question, combined_text)
        
        if decision:
            return {
                "phenomenon": decision.issue_summary,
                "evidence_analysis": [],
                "causal_chain": decision.causal_chain,
                "root_cause": decision.causal_chain.get("root_cause", decision.issue_summary),
                "confidence": decision.confidence_score,
                "confidence_reason": f"规则匹配: {decision.matched_rules}",
                "alternative_causes": []
            }
        
        # 通用回退
        layer_str = layer.value if layer else "L2"
        return {
            "phenomenon": question[:100],
            "evidence_analysis": [],
            "causal_chain": {
                "trigger": "待进一步分析",
                "mechanism": "待进一步分析",
                "manifestation": question[:100]
            },
            "root_cause": f"[{layer_str}层] 需要更多证据才能确定根本原因",
            "confidence": 0.3,
            "confidence_reason": "证据不足",
            "alternative_causes": []
        }
    
    def _build_decision(
        self,
        layer: Optional[Layer],
        evidence_items: List[EvidenceItem],
        rca_result: Dict
    ) -> DeterministicDecision:
        """构建决策对象"""
        collected = [e for e in evidence_items if e.collected]
        missing = [e for e in evidence_items if not e.collected]
        
        confidence_score = rca_result.get("confidence", 0.5)
        confidence = Confidence.from_score(confidence_score)
        
        return DeterministicDecision(
            layer=layer or Layer.L2,
            scenario=rca_result.get("phenomenon", "")[:50],
            category="LLMAnalysis" if self.holmes_service else "RuleAnalysis",
            confidence=confidence,
            confidence_score=confidence_score,
            issue_found=True,
            issue_summary=rca_result.get("root_cause", ""),
            context={},
            matched_rules=[],
            excluded_rules=[],
            collected_evidence=[e.id for e in collected],
            missing_evidence=[e.description for e in missing],
            critical_missing=[
                e.description for e in missing 
                if e.level == EvidenceLevel.CRITICAL
            ],
            evidence_details=[],
            causal_chain=rca_result.get("causal_chain", {}),
            remediation_steps=[],
            verification_steps=[],
            next_steps=[],
            facts=[]
        )
