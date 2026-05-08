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
from app.core.workflow.schemas import RCAOutput
from app.core.workflow.state import WorkflowState
from app.core.skills.models import (
    Layer, DeterministicDecision, EvidenceItem,
    EvidenceLevel, Confidence
)
from app.core.prompts import get_workflow_prompt
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
    
    @property
    def node_id(self) -> str:
        return "rca"
    
    @property
    def node_name(self) -> str:
        return "根因分析"

    def _get_prompt_language(self) -> str:
        if self.holmes_service and hasattr(self.holmes_service, "get_prompt_language"):
            return self.holmes_service.get_prompt_language()
        return "zh"

    def _get_rca_prompt(self) -> str:
        return get_workflow_prompt("rca", prompt_language=self._get_prompt_language())
    
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
                        f"layer_handoff长度={len(json.dumps(state.get('layer_handoff') or {}, ensure_ascii=False, default=str))}")

            evidence_summary = self._build_rca_context(state)
            missing_primary = self._get_missing_primary_pod_conflict(state)
            if missing_primary:
                rca_result = self._build_primary_pod_missing_result(
                    question=question,
                    layer=layer,
                    missing_primary=missing_primary,
                    evidence_summary=evidence_summary,
                )
                thinking_events = []
            else:
                rca_result = None
                thinking_events = []

            # 使用 LLM 分析
            ai_call = getattr(self, 'ai_call', None)
            if rca_result is not None:
                pass
            elif ai_call is not None:
                rca_result, thinking_events = self._analyze_with_llm(
                    question, layer, evidence_summary
                )
            else:
                # 无 LLM 时仅保留通用低置信度兜底
                logger.info("⚠️ 无 LLM 服务，使用通用低置信度兜底")
                rca_result = self._build_llm_fallback(
                    question=question,
                    layer=layer,
                    reason="LLM 不可用，无法完成可靠根因分析",
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

    @staticmethod
    def _get_missing_primary_pod_conflict(state: WorkflowState) -> Optional[Dict[str, str]]:
        layer_handoff = state.get("layer_handoff") or {}
        primary = layer_handoff.get("primary_pod") or state.get("primary_pod") or {}
        primary_name = str(primary.get("name") or "")
        primary_namespace = str(primary.get("namespace") or "")
        if not primary_name:
            return None

        for conflict in state.get("evidence_conflicts") or []:
            if not isinstance(conflict, dict) or not conflict.get("object_missing"):
                continue
            obj = conflict.get("object") or {}
            if obj.get("kind") == "Pod" and obj.get("name") == primary_name:
                return {"name": primary_name, "namespace": obj.get("namespace") or primary_namespace}
        return None

    def _build_primary_pod_missing_result(
        self,
        question: str,
        layer: Optional[Layer],
        missing_primary: Dict[str, str],
        evidence_summary: str,
    ) -> Dict[str, Any]:
        layer_str = layer.value if hasattr(layer, "value") else str(layer or "UNKNOWN")
        pod_name = missing_primary.get("name", "")
        namespace = missing_primary.get("namespace", "")
        reason = (
            f"primary_pod {namespace}/{pod_name} 当前已不存在；"
            "上游历史 Event 或归档摘要不能证明该 Pod 仍处于异常状态"
        )
        return {
            "phenomenon": f"目标 Pod {namespace}/{pod_name} 当前不存在，无法确认仍异常",
            "evidence_inventory": [
                {
                    "id": "conflict_primary_pod_missing",
                    "content": reason,
                    "source": "evidence_conflicts",
                    "reliability": "高",
                }
            ],
            "evidence_analysis": [
                {
                    "evidence_id": "conflict_primary_pod_missing",
                    "raw_data": reason,
                    "interpretation": "当前对象不存在是硬冲突，应停止对该历史 Pod 生成 OOM/ImagePull/CrashLoop 等当前根因",
                }
            ],
            "causal_chain": {
                "root_cause": "目标 Pod 已不存在或已恢复，当前无法基于该 Pod 确认故障",
                "propagation": "历史事件被带入诊断上下文，但当前状态验证返回 NotFound",
                "direct_cause": "primary_pod 当前不存在",
                "manifestation": "诊断目标与当前集群状态不一致",
            },
            "root_cause": f"[{layer_str}] 目标 Pod {namespace}/{pod_name} 当前不存在，不能继续诊断为当前故障",
            "root_cause_summary": reason,
            "confidence": 0.2,
            "primary_runbooks": [],
            "alternative_causes": ["历史事件残留", "Pod 已被删除", "工作负载已滚动替换为新 Pod"],
            "limitations": "需要重新从当前异常 Pod 列表选择仍存在的对象后再做 RCA。",
        }
    
    def _build_evidence_summary(self, evidence_items: List[EvidenceItem]) -> str:
        """构建证据摘要"""
        lines = []
        for i, item in enumerate(evidence_items, 1):
            status = "✅ 已采集" if item.collected else "❌ 未采集"
            value = f"= {item.value}" if item.value else ""
            lines.append(f"{i}. [{status}] {item.description} {value}")
        return "\n".join(lines) if lines else "暂无证据"

    def _build_rca_context(self, state: WorkflowState) -> str:
        """Build compact RCA input from handoff + bounded evidence facts."""
        evidence_items = state.get("evidence_items", [])
        evidence_analysis = state.get("evidence_analysis", "{}")
        layer_handoff = state.get("layer_handoff")
        if not layer_handoff:
            layer_handoff = self._layer_analysis_to_handoff(state.get("layer_analysis", ""))

        parts = [
            "# 问题定位结构化交接 layer_handoff",
            json.dumps(layer_handoff or {}, ensure_ascii=False, indent=2, default=str),
            "",
            "# 证据采集结果",
            self._build_evidence_summary(evidence_items),
        ]

        facts = state.get("evidence_facts") or []
        conflicts = state.get("evidence_conflicts") or []
        missing = state.get("missing_evidence") or []
        if facts:
            parts.extend(["", "# 已验证事实", json.dumps(facts, ensure_ascii=False, indent=2, default=str)])
        if conflicts:
            parts.extend(["", "# 冲突/负向证据", json.dumps(conflicts, ensure_ascii=False, indent=2, default=str)])
        if missing:
            parts.extend(["", "# 缺失证据", json.dumps(missing, ensure_ascii=False, indent=2, default=str)])

        extra_data = self._extract_tool_data_for_rca(evidence_analysis)
        if extra_data:
            parts.extend(["", "# 工具采集摘要", extra_data])

        return "\n".join(parts)

    @staticmethod
    def _layer_analysis_to_handoff(layer_analysis: str) -> Dict[str, Any]:
        try:
            data = json.loads(layer_analysis) if layer_analysis else {}
            if isinstance(data, dict):
                return {
                    "layer": data.get("layer"),
                    "derived_layer": data.get("derived_layer", data.get("layer")),
                    "confidence": data.get("confidence"),
                    "primary_problem": data.get("reasoning", ""),
                    "primary_pod": data.get("primary_pod"),
                    "abnormal_pods": data.get("abnormal_pods", []),
                    "pod_status_keyword": data.get("pod_status_keyword"),
                    "pod_abnormal_type": data.get("pod_abnormal_type"),
                    "status_category": data.get("status_category"),
                    "active_entities": data.get("key_entities", []),
                    "possible_scenarios": data.get("possible_scenarios", []),
                    "matched_runbooks": data.get("matched_runbooks", []),
                }
        except (json.JSONDecodeError, TypeError):
            pass
        return {}
    
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
            system_prompt = self._get_rca_prompt().format(
                layer=layer_str,
                evidence_summary="证据上下文只在 user message 中提供，system prompt 不承载动态证据。"
            )

            user_message = f"""# 用户问题
{question}

# 已采集证据
{evidence_summary}

请直接基于以上证据进行根因分析，输出 JSON 格式结果。"""
            self._archive_node_input({
                "node": self.node_id,
                "mode": "lite",
                "question": question,
                "user_message": user_message,
                "evidence_summary": evidence_summary,
                "system_prompt_chars": len(system_prompt),
                "user_message_chars": len(user_message),
            })

            start_time = time.time()

            ai_call = getattr(self, 'ai_call', None)
            if ai_call is None:
                raise RuntimeError("[rca] ai_call 未设置，无法执行 lite 模式")

            logger.info("📍 [rca] Pydantic structured lite 模式开始")
            parsed = None
            content = ""
            if not hasattr(ai_call, "call_structured"):
                raise RuntimeError("[rca] ai_call 不支持 call_structured，无法生成 Pydantic RCAOutput")
            structured, content = ai_call.call_structured(
                system_prompt=system_prompt,
                question=user_message,
                schema=RCAOutput,
                node_id=self.node_id,
                run_id=getattr(self, "current_run_id", ""),
            )
            if structured is not None:
                parsed = structured.model_dump()

            duration_ms = (time.time() - start_time) * 1000

            if self.metrics:
                self.metrics.record_llm_call("rca", duration_ms)

            logger.info("✅ [rca] lite 模式完成 (%.0fms, 输出=%d字)",
                       duration_ms, len(content or ""))

            if parsed:
                return parsed, []

            logger.warning("⚠️ [rca] lite 模式未返回合法 Pydantic RCAOutput，使用通用低置信度兜底")
            return self._build_llm_fallback(
                question=question,
                layer=layer,
                reason="LLM 返回结果不符合 RCA 结构化输出合同",
            ), []

        except Exception as e:
            logger.warning(f"[rca] lite 模式失败，使用通用低置信度兜底: {e}")
            return self._build_llm_fallback(
                question=question,
                layer=layer,
                reason=f"LLM 根因分析失败: {str(e)}",
            ), []

    def _archive_node_input(self, payload: Dict) -> None:
        run_id = getattr(self, "current_run_id", "")
        if not run_id:
            return
        try:
            from app.core.context.archive import ContextArchive

            ContextArchive(run_id=run_id).write_node_artifacts(
                node_id=self.node_id,
                input_payload=payload,
            )
        except Exception as exc:
            logger.warning("⚠️ [rca] 写入 node input archive 失败: %s", exc)

    def _analyze_with_llm_full(
        self,
        question: str,
        layer: Optional[Layer],
        evidence_summary: str
    ) -> tuple:
        """full 模式：原有 _call_llm 全工具调用"""
        try:
            layer_str = layer.value if layer else "L2"

            system_prompt = self._get_rca_prompt().format(
                layer=layer_str,
                evidence_summary=evidence_summary
            )

            # 告诉 LLM 不要重复采集数据，基于已有证据分析
            system_prompt += """

# ⚠️ 重要：不要重复采集数据
上面的「已采集证据」和「工具采集的原始数据」已经包含了所有需要的信息。
请直接基于这些数据进行分析，**不要重新调用工具采集数据**。
如果数据不足，在 limitations 中说明即可。"""

            response, thinking_events = self._call_llm(
                question,
                system_prompt,
                expect_json=True,
                json_validator=lambda data: isinstance(data, dict),
            )

            if response and response.result:
                return self._parse_llm_response(response.result), thinking_events

            return self._build_llm_fallback(
                question=question,
                layer=layer,
                reason="LLM 未返回有效结果，无法完成可靠根因分析",
            ), thinking_events

        except Exception as e:
            logger.warning(f"LLM 分析失败，使用通用低置信度兜底: {e}")
            return self._build_llm_fallback(
                question=question,
                layer=layer,
                reason=f"LLM 根因分析失败: {str(e)}",
            ), []
    
    @staticmethod
    def _normalize_rca_result(parsed: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(parsed, dict):
            return None
        try:
            return RCAOutput.model_validate(parsed).model_dump()
        except Exception as exc:
            logger.warning("⚠️ [rca] RCA 结构化校验失败: %s", exc)
            return None

    def _parse_llm_response(self, response_text: str) -> Dict:
        """解析 LLM 的 JSON 响应"""
        try:
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(1))
            else:
                parsed = json.loads(response_text)
            normalized = self._normalize_rca_result(parsed)
            if normalized is not None:
                return normalized
            return self._build_llm_fallback(
                question="",
                layer=None,
                reason="LLM 返回 JSON 但不符合 RCA 结构化输出合同",
            )
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
    
    def _build_llm_fallback(
        self,
        question: str,
        layer: Optional[Layer],
        reason: str,
    ) -> Dict:
        """LLM 不可用或未返回有效结构化结果时的通用低置信度回退。"""
        layer_str = layer.value if layer else "L2"
        question_short = truncate_question(question)
        return {
            "phenomenon": question_short,
            "evidence_analysis": [],
            "causal_chain": {
                "trigger": "LLM 未生成可靠因果链",
                "mechanism": "缺少可用的结构化根因分析结果",
                "manifestation": question_short
            },
            "root_cause": f"[{layer_str}层] 当前无法基于 LLM 输出确定根本原因",
            "confidence": 0.1,
            "confidence_reason": reason,
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
            category="DataQuery" if is_query else "LLMAnalysis",
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
                tool_parts = []
                index = 1
                for td in tool_data[:10]:
                    tool = td.get("tool", "unknown")
                    if str(tool).lower() in {"read_context_archive", "fetch_runbook"}:
                        continue
                    raw = td.get("data", "")[:500]
                    tool_parts.append(f"{index}. [{tool}]: {raw}")
                    index += 1
                if tool_parts:
                    parts.append("## 工具原始输出")
                    parts.extend(tool_parts)

            return "\n".join(parts)
        except (json.JSONDecodeError, TypeError):
            return ""
