"""
快速检测节点

职责：
- 使用 LLM 循环检测集群中的所有问题
- 不依赖固定场景列表，动态发现所有异常
- 记录每个发现的问题供后续分析
- 最小侵入，与现有 4 节点工作流解耦

设计原则：
- 使用 memory 机制迭代查询
- LLM 驱动，非固定场景
- 记录所有发现的问题
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.state import WorkflowState
from app.core.prompts import GLOBAL_SCENARIO_DETECTOR_PROMPT
from app.core.skills.models import Layer
from app.core.workflow.multi_scenario.output import ScenarioSeverity

logger = logging.getLogger(__name__)


@dataclass
class QuickDetectionItem:
    """快速检测项 - 单个检测到的问题"""

    id: str                    # 唯一标识
    name: str                  # 问题名称
    layer: Layer               # 所在层级
    severity: ScenarioSeverity  # 严重程度
    confidence: float          # 置信度 (0-1)
    summary: str               # 问题摘要
    affected_entities: Dict[str, Any]  # 受影响的实体
    key_evidence: List[str]    # 关键证据

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result["layer"] = str(self.layer)
        result["severity"] = str(self.severity)
        return result


class QuickDetectionNode(WorkflowNode):
    """
    快速检测节点

    使用 LLM 循环检测集群中的所有问题
    """

    def __init__(self, holmes_service: Any = None, max_iterations: int = 5):
        """
        初始化快速检测节点

        Args:
            holmes_service: HolmesService 实例（用于 LLM 调用）
            max_iterations: 最大迭代次数（防止无限循环）
        """
        super().__init__()

        self.holmes_service = holmes_service
        self.max_iterations = max_iterations

    @property
    def node_id(self) -> str:
        return "quick_detector"

    @property
    def node_name(self) -> str:
        return "快速检测"

    def get_required_fields(self) -> List[str]:
        return ["question"]

    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        执行快速检测

        流程：
        1. 获取用户问题
        2. 循环调用 LLM 检测问题
        3. 记录每个发现的问题
        4. 直到 LLM 说"没有其他问题"或达到最大迭代次数
        """
        new_state: WorkflowState = {
            "current_node": self.node_id,
        }

        try:
            question = state.get("question", "")
            logger.info(f"🔍 快速检测开始: {question[:100]}...")

            # 1. 收集集群初始状态（调用基础命令）
            cluster_state = self._collect_cluster_state(question)

            # 2. 循环检测问题
            detected_issues = []
            iteration = 0
            has_more_problems = True

            while has_more_problems and iteration < self.max_iterations:
                iteration += 1
                logger.info(f"  检测轮次 {iteration}/{self.max_iterations}")

                # 构建 prompt，包含已检测到的问题
                prompt = self._build_detection_prompt(
                    question=question,
                    cluster_state=cluster_state,
                    previous_issues=detected_issues
                )

                # 调用 LLM 检测问题
                llm_result = self._call_llm_for_detection(prompt)

                if llm_result:
                    # 解析 LLM 返回的问题
                    issues = self._parse_llm_detection_result(llm_result)

                    if not issues:
                        # 没有新问题，结束检测
                        logger.info(f"  ✅ LLM 未检测到新问题，检测结束")
                        has_more_problems = False
                    else:
                        # 记录新问题
                        for issue in issues:
                            # 检查是否重复
                            if not self._is_duplicate_issue(issue, detected_issues):
                                detected_issues.append(issue)
                                logger.info(f"    🔍 发现新问题: {issue.name} ({issue.layer}, {issue.severity})")
                            else:
                                logger.debug(f"    ⏭️ 跳过重复问题: {issue.name}")
                else:
                    logger.warning(f"  ⚠️ LLM 调用失败，停止检测")
                    has_more_problems = False

            # 3. 输出检测结果
            logger.info(f"✅ 快速检测完成: 发现 {len(detected_issues)} 个问题")

            new_state.update({
                "quick_detection_decisions": [issue.to_dict() for issue in detected_issues],
                "quick_detection_count": len(detected_issues),
            })

        except Exception as e:
            logger.error(f"❌ 快速检测失败: {e}", exc_info=True)
            new_state.setdefault("errors", []).append(
                f"节点 {self.node_id} 执行失败: {str(e)}"
            )

        return new_state

    def _collect_cluster_state(self, question: str) -> Dict[str, Any]:
        """
        收集集群初始状态

        Args:
            question: 用户问题

        Returns:
            集群状态字典
        """
        cluster_state = {
            "question": question,
        }

        # 如果有 holmes_service，使用它调用工具
        if self.holmes_service:
            try:
                # 调用基础命令获取集群状态
                commands = [
                    "kubectl get nodes -o wide",
                    "kubectl get pods -A | grep -E '(Error|CrashLoop|Pending|ImagePullBackOff)'",
                    "kubectl get events -A --sort-by='.lastTimestamp' | head -50",
                ]

                for cmd in commands:
                    try:
                        result = self._run_kubectl_command(cmd)
                        if result:
                            # 从命令中提取关键信息
                            key = cmd.split()[2]  # 资源类型
                            cluster_state[key] = result
                    except Exception as e:
                        logger.debug(f"命令执行失败: {cmd}: {e}")

            except Exception as e:
                logger.warning(f"收集集群状态失败: {e}")

        return cluster_state

    def _build_detection_prompt(
        self,
        question: str,
        cluster_state: Dict[str, Any],
        previous_issues: List[QuickDetectionItem]
    ) -> str:
        """
        构建检测 prompt

        Args:
            question: 用户问题
            cluster_state: 集群状态
            previous_issues: 之前检测到的问题

        Returns:
            构建的 prompt
        """
        # 基础 prompt
        prompt = GLOBAL_SCENARIO_DETECTOR_PROMPT

        # 添加问题上下文
        prompt += f"""

# 当前用户问题
{question}

# 集群当前状态（简要）
"""

        # 添加集群状态摘要
        if "nodes" in cluster_state:
            node_count = cluster_state["nodes"].count("\n") - 1
            prompt += f"- 节点数量: {node_count}\n"

        if "pods" in cluster_state:
            pod_lines = cluster_state["pods"].split("\n")
            error_pods = [line for line in pod_lines if "Error" in line or "CrashLoop" in line]
            prompt += f"- 异常 Pod 数量: {len(error_pods)}\n"

        # 添加已检测到的问题
        if previous_issues:
            prompt += "\n# 已检测到的问题（请在继续检测时避免重复）\n"
            for i, issue in enumerate(previous_issues, 1):
                prompt += f"{i}. [{issue.layer}] {issue.name}: {issue.summary}\n"

        # 添加检测指令
        prompt += """

# 检测指令

请你基于以上信息，检测集群中存在的所有问题。

**重要**：
1. 不要只关注用户提到的问题，要系统性地检查整个集群
2. 如果已经检测到 X 个问题，继续问自己："还有其他问题吗？"
3. 按严重程度排序：Critical > High > Medium > Low
4. 只输出**新发现的问题**（不包含已检测到的问题）

# 输出格式

如果发现新问题，按以下 JSON 格式输出：

```json
{
  "has_more_issues": true,
  "issues": [
    {
      "id": "唯一标识（如: L0-DiskFull, L2-OOMKilled）",
      "name": "问题名称",
      "layer": "L0/L1/L2/L3/L4",
      "severity": "critical/high/medium/low",
      "confidence": 0.0-1.0,
      "summary": "问题摘要（一句话描述）",
      "affected_entities": {
        "pods": ["pod1", "pod2"],
        "nodes": ["node1"],
        "namespaces": ["ns1"]
      },
      "key_evidence": ["证据1", "证据2"]
    }
  ]
}
```

如果没有新问题：

```json
{
  "has_more_issues": false,
  "issues": []
}
```
"""

        return prompt

    def _call_llm_for_detection(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        调用 LLM 进行检测

        Args:
            prompt: 检测 prompt

        Returns:
            LLM 返回的解析结果
        """
        if not self.holmes_service:
            logger.warning("HolmesService 未提供，跳过 LLM 检测")
            return None

        try:
            # 调用 LLM
            response = self.holmes_service._call_llm_with_tools(
                messages=[{"role": "user", "content": prompt}],
                tools=None,
                tool_choice=None,
                temperature=0.1
            )

            if response:
                response_text = response.get("content", "")
                return self._parse_llm_json(response_text)

        except Exception as e:
            logger.error(f"LLM 检测失败: {e}", exc_info=True)

        return None

    def _parse_llm_detection_result(self, llm_result: Dict[str, Any]) -> List[QuickDetectionItem]:
        """
        解析 LLM 检测结果

        Args:
            llm_result: LLM 返回的 JSON

        Returns:
            检测到的问题列表
        """
        issues = []

        try:
            if not llm_result.get("has_more_issues", False):
                return []

            for issue_data in llm_result.get("issues", []):
                try:
                    # 解析 layer
                    layer_str = issue_data.get("layer", "L2")
                    layer = Layer[layer_str]

                    # 解析 severity
                    severity_str = issue_data.get("severity", "medium")
                    severity = ScenarioSeverity(severity_str)

                    issue = QuickDetectionItem(
                        id=issue_data.get("id", f"issue-{len(issues)}"),
                        name=issue_data.get("name", "未知问题"),
                        layer=layer,
                        severity=severity,
                        confidence=issue_data.get("confidence", 0.5),
                        summary=issue_data.get("summary", ""),
                        affected_entities=issue_data.get("affected_entities", {}),
                        key_evidence=issue_data.get("key_evidence", [])
                    )
                    issues.append(issue)

                except Exception as e:
                    logger.error(f"解析单个问题失败: {e}")

        except Exception as e:
            logger.error(f"解析 LLM 检测结果失败: {e}")

        return issues

    def _parse_llm_json(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        解析 LLM 返回的 JSON

        Args:
            response_text: LLM 返回的文本

        Returns:
            解析后的 JSON 字典
        """
        import json
        import re

        try:
            # 尝试直接解析
            return json.loads(response_text)

        except json.JSONDecodeError:
            # 尝试提取 JSON 代码块
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            # 尝试提取第一个 JSON 对象
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

        logger.error(f"无法解析 LLM JSON: {response_text[:200]}...")
        return None

    def _is_duplicate_issue(self, new_issue: QuickDetectionItem, existing_issues: List[QuickDetectionItem]) -> bool:
        """
        检查是否重复的问题

        Args:
            new_issue: 新检测到的问题
            existing_issues: 已存在的问题列表

        Returns:
            是否重复
        """
        for existing in existing_issues:
            # 如果 ID 相同，认为是重复
            if existing.id == new_issue.id:
                return True

            # 如果 layer 和 name 相同，可能是重复
            if existing.layer == new_issue.layer and existing.name == new_issue.name:
                return True

        return False

    def _run_kubectl_command(self, cmd: str) -> Optional[str]:
        """执行 kubectl 命令"""
        import subprocess

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                cwd="/root"
            )

            if result.returncode == 0:
                return result.stdout

        except subprocess.TimeoutExpired:
            logger.warning(f"命令超时: {cmd}")
        except Exception as e:
            logger.error(f"命令执行失败: {cmd}: {e}")

        return None


# ============================================================================
# 全局检测器名称常量
# ============================================================================
GLOBAL_DETECTOR_NODE_ID = "global_detector"
QUICK_DETECTOR_NODE_ID = "quick_detector"
DEEP_ANALYZER_NODE_ID = "deep_analyzer"
