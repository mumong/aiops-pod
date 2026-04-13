"""
节点3：根因分析

职责：
- 调用 LLM 基于证据进行根因推理
- 构建因果链
- 输出：root_cause, causal_chain, rca_analysis

设计：
- 有自己的专用 prompt
- 支持两种 LLM 调用模式（通过 config/环境变量切换）：
  - lite: AICall.call_simple 直接调用（不带工具），避免重复采集
  - full: AICall.call 全工具模式（LangChain create_agent）
- 结合规则引擎验证结论
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.state import WorkflowState
from app.core.skills.models import (
    Layer, DeterministicDecision, EvidenceItem,
    EvidenceLevel, Confidence
)
from app.core.skills.engine import get_engine
from app.core.skills.gate import apply_gate
from app.core.prompts import ROOT_CAUSE_ANALYZER_PROMPT
from app.core.text_helpers import truncate_question

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
            logger.debug(f"🔍 [DEBUG] RCA 输入: question={question[:100]}, "
                        f"evidence_analysis长度={len(evidence_analysis)}, "
                        f"layer_full_analysis长度={len(state.get('layer_full_analysis', ''))}")

            # 构建证据摘要（包含实际工具数据）
            evidence_summary = self._build_evidence_summary(evidence_items)

            # 注入上游 layer 节点的分析结果
            # 优先使用阶段1完整分析文本（含工具输出），回退到结构化 JSON
            layer_analysis = state.get("layer_full_analysis", "") or state.get("layer_analysis", "")
            if layer_analysis:
                evidence_summary = (
                    f"# 问题定位结果（layer 节点输出）\n{layer_analysis}\n\n"
                    f"# 证据采集结果\n{evidence_summary}"
                )

            # 追加 evidence 节点的 LLM 分析和工具数据
            extra_data = self._extract_tool_data_for_rca(evidence_analysis)
            if extra_data:
                evidence_summary += "\n\n# 工具采集的原始数据\n" + extra_data
            
            # 使用 LLM 分析
            ai_call = getattr(self, 'ai_call', None)
            if ai_call is not None:
                rca_result, thinking_events = self._analyze_with_llm(
                    question, layer, evidence_summary
                )
            else:
                # 回退到规则引擎
                logger.info("⚠️ 无 LLM 服务，使用规则引擎")
                rca_result = self._analyze_with_rules(
                    question, layer, evidence_items
                )
                thinking_events = []
            
            # 构建决策对象
            decision = self._build_decision(layer, evidence_items, rca_result)
            
            new_state.update({
                "deterministic_decision": decision,
                "root_cause": rca_result.get("root_cause", ""),
                "causal_chain": rca_result.get("causal_chain", {}),
                "rca_analysis": json.dumps(rca_result, ensure_ascii=False),
                # AI 判定的核心 Runbook（从 primary_runbooks 列表取第一个）
                "primary_runbook_id": ", ".join(rca_result.get("primary_runbooks", []) or []) or None,
            })

            # 存入 thinking_events（带 node 标记）
            self._save_thinking(state, new_state, thinking_events)

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
            self._save_thinking(state, new_state, [])

        return new_state
    
    def _build_evidence_summary(self, evidence_items: List[EvidenceItem]) -> str:
        """构建证据摘要"""
        lines = []
        for i, item in enumerate(evidence_items, 1):
            status = "✅ 已采集" if item.collected else "❌ 未采集"
            value = f"= {item.value}" if item.value else ""
            lines.append(f"{i}. [{status}] {item.description} {value}")
        return "\n".join(lines) if lines else "暂无证据"
    
    def _get_rca_mode(self) -> str:
        """
        获取 RCA 调用模式，优先级: 环境变量 > config.yaml > 默认值(lite)

        Returns:
            "lite" 或 "full"
        """
        # 1. 环境变量
        env_val = os.getenv("WORKFLOW_RCA_MODE", "").lower()
        if env_val in ("lite", "full"):
            return env_val
        # 2. config.yaml → workflow.rca_mode
        if self.holmes_service:
            wf_config = getattr(self.holmes_service, "workflow_config", {}) or {}
            config_val = wf_config.get("rca_mode", "")
            if str(config_val).lower() in ("lite", "full"):
                return str(config_val).lower()
        # 3. 默认 lite（不带工具，避免重复执行）
        return "lite"

    def _analyze_with_llm(
        self,
        question: str,
        layer: Optional[Layer],
        evidence_summary: str
    ) -> tuple:
        """使用 LLM 进行根因分析（自动路由 lite/full 模式）

        Returns:
            (rca_result_dict, intermediate_events_list)
        """
        mode = self._get_rca_mode()
        logger.info(f"🔍 RCA 调用模式: {mode}")

        if mode == "lite":
            return self._analyze_with_llm_lite(question, layer, evidence_summary)
        else:
            return self._analyze_with_llm_full(question, layer, evidence_summary)

    def _analyze_with_llm_lite(
        self,
        question: str,
        layer: Optional[Layer],
        evidence_summary: str
    ) -> tuple:
        """lite 模式：AICall.call_simple 直接调用（不带工具），避免重复采集"""
        try:
            layer_str = layer.value if layer else "L2"
            system_prompt = ROOT_CAUSE_ANALYZER_PROMPT.format(
                layer=layer_str,
                evidence_summary=evidence_summary
            )

            user_message = f"""# 用户问题
{question}

# 已采集证据
{evidence_summary}

请直接基于以上证据进行根因分析，输出 JSON 格式结果。"""

            start_time = time.time()

            ai_call = getattr(self, 'ai_call', None)
            if ai_call is None:
                raise RuntimeError("[rca] ai_call 未设置，无法执行 lite 模式")

            logger.info("📍 [rca] AICall.call_simple lite 模式开始")
            content = ai_call.call_simple(
                system_prompt=system_prompt,
                question=user_message,
            )

            duration_ms = (time.time() - start_time) * 1000

            if self.metrics:
                self.metrics.record_llm_call("rca", duration_ms)

            logger.info("✅ [rca] lite 模式完成 (%.0fms, 输出=%d字)",
                       duration_ms, len(content or ""))

            if content:
                return self._parse_llm_response(content), []

            logger.warning("⚠️ [rca] lite 模式无输出，使用规则兜底")
            return self._analyze_with_rules(question, layer, []), []

        except Exception as e:
            logger.warning(f"[rca] lite 模式失败，回退到规则: {e}")
            return self._analyze_with_rules(question, layer, []), []

    def _analyze_with_llm_full(
        self,
        question: str,
        layer: Optional[Layer],
        evidence_summary: str
    ) -> tuple:
        """full 模式：原有 _call_llm 全工具调用"""
        try:
            layer_str = layer.value if layer else "L2"

            system_prompt = ROOT_CAUSE_ANALYZER_PROMPT.format(
                layer=layer_str,
                evidence_summary=evidence_summary
            )

            # 告诉 LLM 不要重复采集数据，基于已有证据分析
            system_prompt += """

# ⚠️ 重要：不要重复采集数据
上面的「已采集证据」和「工具采集的原始数据」已经包含了所有需要的信息。
请直接基于这些数据进行分析，**不要重新调用工具采集数据**。
如果数据不足，在 limitations 中说明即可。"""

            response, thinking_events = self._call_llm(question, system_prompt)

            if response and response.result:
                return self._parse_llm_response(response.result), thinking_events

            return self._analyze_with_rules(question, layer, []), thinking_events

        except Exception as e:
            logger.warning(f"LLM 分析失败，回退到规则: {e}")
            return self._analyze_with_rules(question, layer, []), []
    
    def _parse_llm_response(self, response_text: str) -> Dict:
        """解析 LLM 的 JSON 响应"""
        try:
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            return json.loads(response_text)
        except json.JSONDecodeError:
            # JSON 解析失败 — 把 LLM 原始文本作为分析结果保留
            # 不要把对话过程塞进 root_cause
            return {
                "phenomenon": "",
                "evidence_analysis": [],
                "causal_chain": {},
                "root_cause": "详见 LLM 原始分析",
                "llm_raw_analysis": response_text,
                "confidence": 0.6,
                "confidence_reason": "LLM 未输出结构化 JSON，使用原始分析文本",
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
        question_short = truncate_question(question)
        return {
            "phenomenon": question_short,
            "evidence_analysis": [],
            "causal_chain": {
                "trigger": "待进一步分析",
                "mechanism": "待进一步分析",
                "manifestation": question_short
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

        # QUERY 模式：非故障，issue_found=False
        is_query = layer == Layer.QUERY

        return DeterministicDecision(
            layer=layer or Layer.L2,
            scenario=rca_result.get("phenomenon", "")[:50],
            category="DataQuery" if is_query else ("LLMAnalysis" if self.holmes_service else "RuleAnalysis"),
            confidence=confidence,
            confidence_score=confidence_score,
            issue_found=not is_query,
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

    def _extract_tool_data_for_rca(self, evidence_analysis: str) -> str:
        """
        从 evidence_analysis JSON 中提取工具采集的真实数据，
        供 RCA prompt 使用，确保根因分析基于实际数据。
        """
        try:
            data = json.loads(evidence_analysis) if isinstance(evidence_analysis, str) else evidence_analysis
            if not isinstance(data, dict):
                return ""

            parts = []

            # 1. LLM 的分析文本（包含工具调用结果的总结）
            llm_analysis = data.get("llm_analysis", "")
            if llm_analysis:
                parts.append(f"## LLM 证据分析\n{llm_analysis[:2000]}")

            # 2. MCP 工具的原始输出
            tool_data = data.get("tool_data", [])
            if tool_data:
                parts.append("## 工具原始输出")
                for i, td in enumerate(tool_data[:10], 1):
                    tool = td.get("tool", "unknown")
                    raw = td.get("data", "")[:500]
                    parts.append(f"{i}. [{tool}]: {raw}")

            return "\n".join(parts)
        except (json.JSONDecodeError, TypeError):
            return ""
