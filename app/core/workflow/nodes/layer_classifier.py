"""
节点1：Pod 异常状态定位（兼容定层）

职责：
- 从用户问题中提取关键实体（Pod、Node、Service 等）
- 调用 LLM 识别当前异常 Pod 状态，并派生兼容 L0-L4 归因层
- 输出：pod_status_keyword, pod_abnormal_type, derived_layer, layer_handoff

设计：
- 有自己的专用 prompt
- 调用 LLM 进行独立分析（使用和 HolmesService 相同的方式）
- 支持使用 runbooks 和 tools
- 输出结构化的分析结果供下游节点使用
"""

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from app.core.context.archive import ContextArchive
from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.schemas import LayerHandoff, LayerOutput, QueryResult
from app.core.workflow.state import WorkflowState
from app.core.skills.models import Layer
from app.core.prompts import get_workflow_prompt

logger = logging.getLogger(__name__)


class LayerClassifierNode(WorkflowNode):
    """
    问题定位节点

    每次执行都会调用 LLM 进行独立分析
    """
    QUERY_DIRECT_BLOCKED_TOOLS = [
        "TodoWrite",
        "collect_aiops_case",
        "get_aiops_case",
        "get_aiops_case_evidence",
        "search_aiops_cases",
    ]
    FULL_DIAGNOSIS_ALLOWED_TOOLS = {
        "kubectl_get_by_kind_in_cluster",
        "kubectl_get_by_name",
        "fetch_runbook",
    }

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
        return "layer"
    
    @property
    def node_name(self) -> str:
        return "问题定位"


    def should_inject_runbook_catalog(self) -> bool:
        # /query direct 模式下只做轻量真实取数，不注入大段 runbook catalog 干扰本地模型工具决策。
        return not self._is_direct_query_mode()

    def _get_query_mode(self) -> str:
        wf_config = getattr(self, "workflow_config_override", None) or {}
        return str(wf_config.get("query_mode", "full")).strip().lower() or "full"

    def _is_direct_query_mode(self) -> bool:
        return self._get_query_mode() == "direct"

    def _is_explicit_pod_early_stop_enabled(self, default: bool = True) -> bool:
        cfg = self._get_workflow_config()
        node_cfg = cfg.get("layer", {}) if isinstance(cfg, dict) else {}
        early_cfg = node_cfg.get("early_stop", {}) if isinstance(node_cfg, dict) else {}
        if isinstance(early_cfg, dict) and "explicit_pod_enabled" in early_cfg:
            return self._parse_bool_config(early_cfg.get("explicit_pod_enabled"), default)
        return default

    def _get_layer_blocked_tool_names(self) -> set[str]:
        return {
            str(getattr(tool, "name", "") or "")
            for tool in (getattr(self, "tools", []) or [])
            if str(getattr(tool, "name", "") or "")
            and str(getattr(tool, "name", "") or "") not in self.FULL_DIAGNOSIS_ALLOWED_TOOLS
        }

    def _get_layer_prompt(self) -> str:
        if self._is_direct_query_mode():
            return get_workflow_prompt("layer_query_direct", prompt_language=self._get_prompt_language())
        return get_workflow_prompt("layer", prompt_language=self._get_prompt_language())

    def _get_layer_extract_prompt(self) -> str:
        if self._is_direct_query_mode():
            return get_workflow_prompt("layer_query_direct_extract", prompt_language=self._get_prompt_language())
        return get_workflow_prompt("layer_extract", prompt_language=self._get_prompt_language())

    def _allow_layer_extract_fallback(self) -> bool:
        runtime_fallback = self._is_structured_runtime_fallback_enabled(default=True)
        cfg = self._get_workflow_config()
        node_cfg = cfg.get("layer", {}) if isinstance(cfg, dict) else {}
        if isinstance(node_cfg, dict):
            if "extract_fallback" in node_cfg:
                return self._parse_bool_config(node_cfg.get("extract_fallback"), runtime_fallback)
            structured_cfg = node_cfg.get("structured_output")
            if isinstance(structured_cfg, dict) and "extract_fallback" in structured_cfg:
                return self._parse_bool_config(structured_cfg.get("extract_fallback"), runtime_fallback)
        return runtime_fallback


    @staticmethod
    def _is_llm_unavailable_text(text: str) -> bool:
        content = str(text or "")
        if "LLM 服务不可用" in content:
            return True
        unavailable_markers = (
            "Agent 执行异常",
            "Connection error",
            "Connection refused",
            "APIConnectionError",
            "Failed to establish a new connection",
            "Could not connect to server",
        )
        return any(marker in content for marker in unavailable_markers) and (
            "Connection" in content or "connect" in content or "连接" in content
        )

    @staticmethod
    def _llm_unavailable_message(raw_error: str) -> str:
        detail = " ".join(str(raw_error or "").split())
        if detail:
            return f"LLM 服务不可用，无法完成问题定位: {detail}"
        return "LLM 服务不可用，无法完成问题定位"

    def _is_usable_query_result(
        self,
        result: Optional[Dict[str, Any]],
        thinking_events: List[Dict[str, Any]],
    ) -> bool:
        if not self._is_structured_layer_result(result):
            return False

        if str(result.get("layer") or "").upper() != "QUERY":
            return True

        query_result = result.get("query_result")
        if not isinstance(query_result, dict):
            return False

        if not self._has_successful_tool_results(thinking_events):
            return False

        try:
            parsed = QueryResult.model_validate(query_result)
        except Exception:
            return False

        return bool(parsed.rows or parsed.missing)

    @classmethod
    def _normalize_query_result_sources(
        cls,
        result: Optional[Dict[str, Any]],
        thinking_events: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """Fill QUERY source metadata from real tool events at the schema boundary.

        Sources are provenance metadata, not the query payload itself. Missing or
        blank sources should not trigger another expensive tool round when rows
        already came from successful tool_results.
        """
        if not isinstance(result, dict):
            return result
        query_result = result.get("query_result")
        if not isinstance(query_result, dict):
            return result

        normalized = dict(result)
        normalized_query_result = dict(query_result)
        current_sources = normalized_query_result.get("sources")
        if cls._has_non_blank_query_sources(current_sources):
            return normalized

        event_sources = cls._query_sources_from_tool_events(thinking_events)
        if event_sources:
            normalized_query_result["sources"] = event_sources
            normalized["query_result"] = normalized_query_result
        return normalized

    @staticmethod
    def _has_non_blank_query_sources(sources: Any) -> bool:
        if not isinstance(sources, list) or not sources:
            return False
        for source in sources:
            if not isinstance(source, dict):
                if str(source or "").strip() and str(source or "").strip() != "-":
                    return True
                continue
            tool = str(source.get("tool") or "").strip()
            query = str(source.get("query") or "").strip()
            if (tool and tool != "-") or (query and query != "-"):
                return True
        return False

    @staticmethod
    def _query_sources_from_tool_events(thinking_events: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        sources: List[Dict[str, str]] = []
        seen = set()
        for ev in thinking_events or []:
            if ev.get("type") != "tool_result" or ev.get("status") != "success":
                continue
            tool_name = str(ev.get("tool_name") or "").strip()
            if not tool_name:
                continue
            if tool_name not in {
                "execute_prometheus_instant_query",
                "execute_prometheus_range_query",
                "kubectl_top_nodes",
                "kubectl_top_pods",
            }:
                continue
            if ev.get("semantic_success", True) is False:
                continue
            tool_args = ev.get("tool_args") or {}
            query = ""
            if isinstance(tool_args, dict):
                query = str(
                    tool_args.get("query")
                    or tool_args.get("promql")
                    or tool_args.get("command")
                    or ""
                ).strip()
            item = {"tool": tool_name, "query": query or "-"}
            key = (item["tool"], item["query"])
            if key in seen:
                continue
            seen.add(key)
            sources.append(item)
        return sources

    @classmethod
    def _query_result_from_prometheus_tool_events(
        cls,
        question: str,
        thinking_events: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """Build QueryResult from real Prometheus tool observations.

        This is a transport/provenance adapter: it only consumes successful
        Prometheus tool_result payloads already archived by AICall. It does not
        infer diagnoses or fabricate query data from model prose.
        """
        rows_by_node: Dict[str, Dict[str, Any]] = {}
        columns: List[Dict[str, str]] = [{"key": "node", "label": "节点"}]
        seen_columns = {"node"}
        sources: List[Dict[str, str]] = []
        query_count = 0
        empty_count = 0

        for ev in thinking_events or []:
            if ev.get("type") != "tool_result" or ev.get("status") != "success":
                continue
            tool_name = str(ev.get("tool_name") or "").strip()
            if tool_name not in {"execute_prometheus_instant_query", "execute_prometheus_range_query"}:
                continue
            if ev.get("semantic_success", True) is False:
                continue
            structured = ev.get("structured") or {}
            if isinstance(structured, dict) and str(structured.get("status") or "").lower() == "prometheus_error":
                continue

            parsed = cls._parse_prometheus_tool_result(ev.get("result") or ev.get("result_preview") or "")
            if parsed is None:
                continue

            tool_args = ev.get("tool_args") or {}
            query = ""
            if isinstance(tool_args, dict):
                query = str(tool_args.get("query") or tool_args.get("promql") or "").strip()
            if cls._is_prometheus_metadata_query(query):
                continue
            query_count += 1
            metric_key, metric_label = cls._prometheus_query_column(query, query_count)
            if metric_key not in seen_columns:
                columns.append({"key": metric_key, "label": metric_label})
                seen_columns.add(metric_key)
            if query:
                sources.append({"tool": tool_name, "query": query})

            vector = (((parsed.get("data") or {}) if isinstance(parsed, dict) else {}).get("result") or [])
            if not isinstance(vector, list) or not vector:
                empty_count += 1
                continue
            for item in vector:
                if not isinstance(item, dict):
                    continue
                node = cls._prometheus_node_key(item.get("metric") or {})
                value = cls._prometheus_sample_value(item.get("value") or item.get("values"))
                if not node or value is None:
                    continue
                row = rows_by_node.setdefault(node, {"node": node})
                row[metric_key] = value

        if not rows_by_node:
            if query_count:
                return QueryResult.model_validate({
                    "query_target": question,
                    "collection_summary": f"计划 {query_count} 项，实际采集 0 项，未采集 {query_count} 项，完整度 0%",
                    "columns": columns,
                    "rows": [],
                    "notes": ["Prometheus 查询成功执行，但结果为空。"],
                    "missing": [{"field": "result", "reason": "Prometheus 返回空 result"}],
                    "sources": sources,
                }).model_dump()
            return None

        rows = list(rows_by_node.values())
        collected = sum(
            1
            for column in columns
            if column["key"] != "node" and any(column["key"] in row for row in rows)
        )
        total = max(len(columns) - 1, query_count)
        missing_count = max(total - collected, 0)
        missing = []
        if missing_count:
            present_keys = {key for row in rows for key in row.keys()}
            for column in columns:
                if column["key"] != "node" and column["key"] not in present_keys:
                    missing.append({"field": column["key"], "reason": "Prometheus 返回结果中没有该指标列"})
        if empty_count and not missing:
            missing.append({"field": "result", "reason": "部分 Prometheus 查询返回空 result"})

        return QueryResult.model_validate({
            "query_target": question,
            "collection_summary": (
                f"计划 {total} 项，实际采集 {collected} 项，"
                f"未采集 {missing_count} 项，完整度 {int((collected / total) * 100) if total else 0}%"
            ),
            "columns": columns,
            "rows": rows,
            "notes": ["数据来自 Prometheus 工具结果；节点字段来自 Prometheus metric.instance/node。"],
            "missing": missing,
            "sources": sources,
        }).model_dump()

    @staticmethod
    def _is_prometheus_metadata_query(query: str) -> bool:
        lowered = (query or "").strip().lower()
        if not lowered:
            return False
        metadata_prefixes = (
            "node_uname_info",
            "kube_node_info",
            "node_boot_time_seconds",
        )
        return any(lowered.startswith(prefix) for prefix in metadata_prefixes)

    @staticmethod
    def _parse_prometheus_tool_result(raw: Any) -> Optional[Dict[str, Any]]:
        if isinstance(raw, dict):
            return raw
        text = str(raw or "").strip()
        if not text:
            return None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) and parsed.get("status") == "success" else None

    @staticmethod
    def _prometheus_query_column(query: str, index: int) -> tuple[str, str]:
        lowered = (query or "").lower()
        if "node_cpu_seconds_total" in lowered:
            return "cpu_usage_percent", "CPU 使用率 (%)"
        if "node_memory_memavailable_bytes" in lowered or "node_memory_memtotal_bytes" in lowered:
            return "memory_usage_percent", "内存使用率 (%)"
        if "node_filesystem" in lowered:
            return "disk_usage_percent", "磁盘使用率 (%)"
        if "node_network_receive" in lowered:
            return "network_receive_bits_per_second", "网络接收 (bits/s)"
        if "node_network_transmit" in lowered:
            return "network_transmit_bits_per_second", "网络发送 (bits/s)"
        return f"metric_{index}", f"指标 {index}"

    @staticmethod
    def _prometheus_node_key(metric: Any) -> str:
        if not isinstance(metric, dict):
            return ""
        return str(metric.get("node") or metric.get("instance") or metric.get("pod") or "").strip()

    @staticmethod
    def _prometheus_sample_value(value: Any) -> Optional[float]:
        sample = None
        if isinstance(value, list) and len(value) >= 2:
            sample = value[1]
        elif isinstance(value, list) and value and isinstance(value[-1], list) and len(value[-1]) >= 2:
            sample = value[-1][1]
        if sample is None:
            return None
        try:
            return round(float(sample), 2)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_layer_output_dict(result: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Normalize enum-like fields at the Pydantic boundary before routing decisions."""
        if not isinstance(result, dict):
            return result
        normalized = dict(result)
        if normalized.get("layer") is not None:
            layer = str(normalized.get("layer") or "").upper()
            normalized["layer"] = "QUERY" if layer == "QUERY_RESULT" else layer
        if normalized.get("derived_layer") is not None:
            derived_layer = str(normalized.get("derived_layer") or "").upper()
            normalized["derived_layer"] = "QUERY" if derived_layer == "QUERY_RESULT" else derived_layer
        layers = normalized.get("layers")
        if isinstance(layers, list):
            normalized["layers"] = [
                "QUERY" if str(item).upper() == "QUERY_RESULT" else str(item).upper()
                for item in layers
                if item
            ]
        query_result = normalized.get("query_result")
        if isinstance(query_result, dict):
            try:
                normalized["query_result"] = QueryResult.model_validate(query_result).model_dump()
            except Exception:
                pass
        return normalized

    def _get_query_retry_prompt(self) -> str:
        return (
            self._get_layer_prompt()
            + "\n\n# 上一轮结果被系统拒绝\n"
              "- 原因：你给出了 QUERY 结论，但没有提供足够的真实工具执行结果。\n"
              "- 本轮必须先执行工具，再让 Pydantic 结构化提取生成最终 query_result。\n"
              "- 在出现至少一次成功的 tool_result 之前，禁止输出最终答案。\n"
              "- 你的最后一条消息必须建立在真实工具结果之上，而不是工具计划之上。\n"
              "- 如果没有至少一次成功的 tool_result，系统会再次拒绝你的输出。\n"
              "- `query_result.rows` 为空且 `missing` 也为空，视为无效结果。\n"
              "- `collection_summary`、`sources`、`rows` 只能基于真实工具结果填写，禁止编造“已采集 100%”。\n"
        )

    def _should_stop_query_direct_early(self, thinking_events: List[Dict[str, Any]]) -> bool:
        """Stop QUERY direct after all in-flight Prometheus queries returned.

        The agent may emit multiple Prometheus tool calls in one model message
        (for example CPU and memory). Stopping on the first result can truncate
        sibling tool calls, so this waits until every started Prometheus call has
        a terminal result. Pydantic extraction then consumes the real tool
        transcript; the agent does not need to spend another minute writing a
        natural-language collection summary.
        """
        prometheus_tools = {"execute_prometheus_instant_query", "execute_prometheus_range_query"}
        started_call_ids = set()
        result_call_ids = set()
        terminal_results = 0
        for ev in thinking_events or []:
            tool_name = str(ev.get("tool_name") or "")
            if tool_name not in prometheus_tools:
                continue
            call_id = str(ev.get("tool_call_id") or "")
            if ev.get("type") == "tool_start":
                if call_id:
                    started_call_ids.add(call_id)
                continue
            if ev.get("type") != "tool_result" or ev.get("status") != "success":
                continue
            if call_id:
                result_call_ids.add(call_id)
            structured = ev.get("structured") or {}
            status = str(structured.get("status") or "").lower()
            if status == "prometheus_error" or ev.get("semantic_success", True) is False:
                terminal_results += 1
                continue
            result = ev.get("result") or ev.get("result_preview") or ""
            if result and re.search(r'"result"\s*:\s*\[|result_count', result, re.IGNORECASE):
                terminal_results += 1
        if not terminal_results:
            return False
        if started_call_ids:
            return started_call_ids.issubset(result_call_ids)
        return False

    @staticmethod
    def _should_stop_explicit_pod_early(
        question: str,
        thinking_events: List[Dict[str, Any]],
    ) -> bool:
        """Stop full diagnosis after the explicitly requested Pod is verified."""
        question_text = str(question or "").lower()
        for event in thinking_events or []:
            if (
                event.get("type") != "tool_result"
                or event.get("status") != "success"
                or event.get("semantic_success", True) is False
                or event.get("tool_name") != "kubectl_get_by_name"
            ):
                continue
            tool_args = event.get("tool_args") or {}
            if not isinstance(tool_args, dict):
                continue
            kind = str(tool_args.get("kind") or "").strip().lower()
            name = str(tool_args.get("name") or "").strip().lower()
            namespace = str(tool_args.get("namespace") or "").strip().lower()
            if kind not in {"pod", "pods"} or not name or not namespace:
                continue
            result = str(event.get("result") or event.get("result_preview") or "").lower()
            if (
                name in question_text
                and namespace in question_text
                and name in result
            ):
                return True
        return False

    def _build_query_direct_failure_result(
        self,
        question: str,
        full_analysis_text: str,
        failure_reason: str,
    ) -> Dict[str, Any]:
        return {
            "layer": "QUERY",
            "layers": ["QUERY"],
            "layer_name": "查询请求",
            "confidence": 0.3,
            "reasoning": failure_reason,
            "key_entities": [],
            "possible_scenarios": [],
            "query_result": {
                "query_target": question,
                "collection_summary": "计划 0 项，实际采集 0 项，未采集 1 项，完整度 0%",
                "columns": [
                    {"key": "status", "label": "状态"},
                    {"key": "reason", "label": "原因"},
                ],
                "rows": [],
                "notes": ["未获得足够的真实工具结果，已拒绝模型直接生成的伪结构化答案。"],
                "missing": [{"field": "query_result", "reason": failure_reason}],
                "sources": [],
            },
            "full_analysis": full_analysis_text,
        }
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        执行定层逻辑

        1. 构建专用 prompt
        2. 调用 LLM 分析
        3. 解析输出，提取层级信息
        """
        question = state.get("question", "")

        new_state: WorkflowState = {
            "current_node": self.node_id,
        }

        try:
            # 如果有 AICall，统一使用 LLM 做 QUERY / HEALTHY / L0-L4 判断
            ai_call = getattr(self, 'ai_call', None)
            if ai_call is not None:
                layer_result, thinking_events = self._analyze_with_llm(question)
            else:
                # 无 LLM 时仅使用低置信度兜底，避免人工关键词主导分类
                logger.info("⚠️ 无 LLM 服务，使用低置信度兜底分类")
                layer_result = self._analyze_with_rules(question)
                thinking_events = []

            # 解析层级
            layer = self._parse_layer(layer_result.get("layer", "ABNORMAL"))

            # 解析多层级（多问题并存）
            raw_layers = layer_result.get("layers", [])
            layers = [self._parse_layer(l) for l in raw_layers if l] if raw_layers else [layer]

            # 提取阶段1的完整分析文本（包含工具调用数据），只归档，不再作为大字段传递给下游
            full_analysis = layer_result.pop("full_analysis", "")
            query_result = layer_result.pop("query_result", None)
            layer_handoff = self._build_layer_handoff(
                question=question,
                layer_result=layer_result,
                layer=layer,
                layers=layers,
                thinking_events=thinking_events,
            )
            layer, layers = self._guard_healthy_with_active_abnormalities(
                layer_result=layer_result,
                layer_handoff=layer_handoff,
                layer=layer,
                layers=layers,
            )
            self._sync_layer_result_from_handoff(layer_result, layer_handoff)
            archive_refs = self._archive_layer_outputs(
                run_id=state.get("run_id", ""),
                full_analysis=full_analysis,
                handoff=layer_handoff,
            )
            if archive_refs.get("full_analysis_ref"):
                layer_handoff["archive_ref"] = archive_refs["full_analysis_ref"]

            new_state.update({
                "layer": layer,
                "layers": layers,
                "layer_confidence": layer_result.get("confidence", 0.5),
                "layer_reasoning": layer_result.get("reasoning", ""),
                # 保存结构化分类结果
                "layer_analysis": json.dumps(layer_result, ensure_ascii=False),
                # 大文本只落盘；下游使用 layer_handoff
            "layer_full_analysis": None,
            "layer_handoff": layer_handoff,
            "layer_archive_ref": archive_refs,
            "context_archive_ref": archive_refs.get("run_root"),
            "issue_groups": layer_handoff.get("issue_groups", []),
            "abnormal_groups": layer_handoff.get("abnormal_groups", layer_handoff.get("issue_groups", [])),
            "abnormal_pods": layer_handoff.get("abnormal_pods", []),
            "pod_status_keyword": layer_handoff.get("pod_status_keyword"),
            "pod_abnormal_type": layer_handoff.get("pod_abnormal_type"),
            "derived_layer": layer_handoff.get("derived_layer"),
                "status_category": layer_handoff.get("status_category"),
                "key_entities": layer_result.get("key_entities", []),
                "possible_scenarios": layer_result.get("possible_scenarios", []),
            })
            if layer == Layer.QUERY and self._is_direct_query_mode():
                self._attach_query_result_or_failure(
                    new_state=new_state,
                    question=question,
                    query_result=query_result,
                    failure_context="QUERY direct 结果结构化校验失败",
                )

            # 存入 thinking_events（带 node 标记）
            self._save_thinking(state, new_state, thinking_events)

            logger.info(f"✅ 问题定位完成: {layer} (置信度: {layer_result.get('confidence', 0):.0%})")

        except Exception as e:
            logger.error(f"问题定位失败: {e}", exc_info=True)
            new_state.setdefault("errors", []).append(
                f"节点 {self.node_id} 执行失败: {str(e)}"
            )
            if self._is_llm_unavailable_text(str(e)):
                raise RuntimeError(self._llm_unavailable_message(str(e))) from e
            rescue_result = self._extract_with_lite_llm(
                question=question,
                full_analysis_text=f"# layer 节点执行异常\n{str(e)}",
                failure_reason=f"layer 节点执行异常: {str(e)}",
            )
            if rescue_result is None:
                raise

            layer = self._parse_layer(rescue_result.get("layer", "HEALTHY"))
            raw_layers = rescue_result.get("layers", [])
            layers = [self._parse_layer(l) for l in raw_layers if l] if raw_layers else [layer]
            full_analysis = rescue_result.pop("full_analysis", "")
            query_result = rescue_result.pop("query_result", None)
            layer_handoff = self._build_layer_handoff(
                question=question,
                layer_result=rescue_result,
                layer=layer,
                layers=layers,
                thinking_events=[],
            )
            layer, layers = self._guard_healthy_with_active_abnormalities(
                layer_result=rescue_result,
                layer_handoff=layer_handoff,
                layer=layer,
                layers=layers,
            )
            self._sync_layer_result_from_handoff(rescue_result, layer_handoff)
            archive_refs = self._archive_layer_outputs(
                run_id=state.get("run_id", ""),
                full_analysis=full_analysis,
                handoff=layer_handoff,
            )
            if archive_refs.get("full_analysis_ref"):
                layer_handoff["archive_ref"] = archive_refs["full_analysis_ref"]

            new_state.update({
                "layer": layer,
                "layers": layers,
                "layer_confidence": rescue_result.get("confidence", 0.5),
                "layer_reasoning": rescue_result.get("reasoning", ""),
                "layer_analysis": json.dumps(rescue_result, ensure_ascii=False),
                "layer_full_analysis": None,
                "layer_handoff": layer_handoff,
                "layer_archive_ref": archive_refs,
                "context_archive_ref": archive_refs.get("run_root"),
                "issue_groups": layer_handoff.get("issue_groups", []),
                "abnormal_groups": layer_handoff.get("abnormal_groups", layer_handoff.get("issue_groups", [])),
                "abnormal_pods": layer_handoff.get("abnormal_pods", []),
                "pod_status_keyword": layer_handoff.get("pod_status_keyword"),
                "pod_abnormal_type": layer_handoff.get("pod_abnormal_type"),
                "derived_layer": layer_handoff.get("derived_layer"),
                "status_category": layer_handoff.get("status_category"),
                "key_entities": rescue_result.get("key_entities", []),
                "possible_scenarios": rescue_result.get("possible_scenarios", []),
            })
            if layer == Layer.QUERY and self._is_direct_query_mode():
                self._attach_query_result_or_failure(
                    new_state=new_state,
                    question=question,
                    query_result=query_result,
                    failure_context="QUERY direct rescue 结果结构化校验失败",
                )
            self._save_thinking(state, new_state, [])

        return new_state

    @staticmethod
    def _attach_query_result_or_failure(
        new_state: WorkflowState,
        question: str,
        query_result: Any,
        failure_context: str,
    ) -> None:
        """Persist QUERY result without allowing schema errors to become diagnosis fallback."""
        if isinstance(query_result, dict):
            try:
                new_state["query_result"] = QueryResult.model_validate(query_result).model_dump()
                return
            except ValidationError as exc:
                failure_reason = f"{failure_context}: {exc}"
        else:
            failure_reason = f"{failure_context}: query_result 缺失或不是对象"

        new_state["query_result"] = QueryResult.model_validate({
            "query_target": question,
            "collection_summary": "查询已识别为 QUERY，但 query_result 结构化校验失败，已阻止误降级为诊断层。",
            "columns": [],
            "rows": [],
            "missing": [{"field": "query_result", "reason": failure_reason}],
            "sources": [],
        }).model_dump()

    @staticmethod
    def _sync_layer_result_from_handoff(layer_result: Dict[str, Any], handoff: Dict[str, Any]) -> None:
        """Keep observable layer_analysis aligned with the factual handoff.

        Pydantic extraction may miss secondary current-state anomalies, while
        handoff merges tool-derived abnormal rows. Persist the merged fields so
        downstream consumers and observability see the same structured facts.
        """
        for key in (
            "abnormal_pods",
            "abnormal_groups",
            "issue_groups",
            "current_abnormal_summary",
            "pod_status_keyword",
            "pod_abnormal_type",
            "status_category",
        ):
            if key in handoff:
                layer_result[key] = handoff.get(key)
        layer_result.pop("primary_pod", None)

    def _archive_layer_outputs(
        self,
        run_id: str,
        full_analysis: str,
        handoff: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Archive full layer text and compact handoff; keep only refs in state."""
        if not run_id:
            return {}
        try:
            archive = ContextArchive(run_id=run_id)
            refs = archive.write_layer_artifacts(full_analysis or "", handoff or {})
            refs["run_root"] = str(archive.root)
            return refs
        except Exception as exc:
            logger.warning("⚠️ [layer] 写入 context archive 失败: %s", exc)
            return {}

    def _build_layer_handoff(
        self,
        question: str,
        layer_result: Dict[str, Any],
        layer: Layer,
        layers: List[Layer],
        thinking_events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build a compact structured handoff for downstream nodes."""
        active_entities = self._normalize_entities(layer_result.get("key_entities", []))
        explicit_pod_scope = self._get_explicit_pod_scope(question, active_entities)
        abnormal_pods = self._normalize_abnormal_pods(
            layer_result.get("abnormal_pods"),
            active_entities,
            layer_result.get("pod_status_keyword"),
        )
        current_abnormal_pods = self._extract_current_abnormal_pods_from_events(thinking_events)
        current_abnormal_summary = self._extract_current_abnormal_summary_from_events(thinking_events)
        if explicit_pod_scope:
            current_abnormal_pods = [
                pod
                for pod in current_abnormal_pods
                if self._pod_matches_scope(pod, explicit_pod_scope)
            ]
            abnormal_pods = [
                pod
                for pod in abnormal_pods
                if self._pod_matches_scope(pod, explicit_pod_scope)
            ]
            current_abnormal_summary = self._scope_abnormal_summary_to_pod(
                current_abnormal_summary,
                explicit_pod_scope,
            )
        if current_abnormal_pods:
            abnormal_pods = self._merge_current_abnormal_pods(abnormal_pods, current_abnormal_pods)
        active_signals = []
        matched_runbooks = []

        for ev in thinking_events or []:
            if ev.get("type") != "tool_result" or ev.get("status") != "success":
                continue
            tool_name = ev.get("tool_name", "unknown")
            if tool_name == "fetch_runbook":
                rb_id = self._extract_runbook_id(ev)
                if rb_id and rb_id not in matched_runbooks:
                    matched_runbooks.append(rb_id)
            if explicit_pod_scope and tool_name == "kubectl_get_by_kind_in_cluster":
                continue

            signal = ev.get("result", "") or ev.get("result_preview", "")
            if signal:
                structured = ev.get("structured") or {}
                key_events = []
                if isinstance(structured, dict):
                    key_events = [
                        str(item)
                        for item in (structured.get("key_events") or structured.get("signals") or [])[:5]
                        if str(item).strip()
                    ]
                active_signals.append({
                    "source": tool_name,
                    "signal": self._compact_signal(signal),
                    "key_events": key_events,
                    "raw_ref": ev.get("raw_ref"),
                    "summary_ref": ev.get("summary_ref"),
                })

        layer_value = layer.value if hasattr(layer, "value") else str(layer)
        pod_abnormal_type = self._derive_pod_abnormal_type(layer_result)
        issue_groups = self._build_issue_groups(
            abnormal_pods=abnormal_pods,
            default_pod_abnormal_type=pod_abnormal_type,
            layer_result=layer_result,
        )
        if explicit_pod_scope:
            must_verify = [
                "本轮仅验证用户明确指定的 namespace + Pod；全局扫描中的其他异常只作为背景",
                "确认目标 Pod 当前仍存在于指定 namespace",
                "确认目标 Pod 的 active_signals 仍能被真实工具结果验证",
                "如果工具返回 NotFound、空事件或 namespace 不匹配，记录为冲突/负向证据",
            ]
        else:
            must_verify = [
                "以 abnormal_groups、abnormal_pods、current_abnormal_summary 为覆盖基准",
                "异常组完整/最小验证由 evidence 节点按 abnormal_groups 覆盖，避免遗漏 Terminating、Pending 等并发异常状态",
                "确认 active_entities 中的对象当前仍存在于指定 namespace",
                "确认 active_signals 仍能被真实工具结果验证",
                "如果工具返回 NotFound、空事件或 namespace 不匹配，记录为冲突/负向证据",
                "如果某个异常 Pod 不在当前异常 Pod 列表中，必须把它视为历史事件噪音而不是当前故障",
            ]
        handoff = {
            "diagnosis_scope": (
                "explicit_pod"
                if explicit_pod_scope
                else "current_state_only"
                if "之前" in question or "当前" in question or "现在" in question
                else "question_scope"
            ),
            "layer": layer_value,
            "derived_layer": self._pick_text(layer_result.get("derived_layer"), layer_value),
            "layers": [l.value if hasattr(l, "value") else str(l) for l in layers],
            "confidence": layer_result.get("confidence", 0.5),
            "primary_problem": layer_result.get("reasoning", ""),
            "abnormal_pods": abnormal_pods,
            "abnormal_groups": issue_groups,
            "issue_groups": issue_groups,
            "current_abnormal_summary": current_abnormal_summary,
            "pod_status_keyword": self._pick_text(
                layer_result.get("pod_status_keyword"),
                abnormal_pods[0].get("status") if abnormal_pods else "",
            ),
            "pod_abnormal_type": pod_abnormal_type,
            "status_category": self._derive_status_category(layer_result, pod_abnormal_type),
            "active_entities": active_entities,
            "active_signals": active_signals[:12],
            "possible_scenarios": layer_result.get("possible_scenarios", []),
            "matched_runbooks": matched_runbooks,
            "must_verify": must_verify,
            "do_not_change": [
                "不要把上游 namespace、Pod、Service、Node 名称改写成其他对象",
                "不要把历史 event 当成当前故障",
                "不要把计划或工具名当成证据，必须基于 tool_result",
            ],
        }
        return LayerHandoff.model_validate(handoff).model_dump(exclude_none=True)

    @classmethod
    def _get_explicit_pod_scope(
        cls,
        question: str,
        active_entities: List[Dict[str, Any]],
    ) -> Optional[tuple[str, str]]:
        text = str(question or "").lower()
        candidates = []
        for entity in active_entities or []:
            if str(entity.get("type") or "").strip().lower() != "pod":
                continue
            namespace = cls._pick_text(entity.get("namespace")).lower()
            name = cls._pick_text(entity.get("name"), entity.get("value")).lower()
            if namespace and name and namespace in text and name in text:
                candidates.append((namespace, name))
        return candidates[0] if len(candidates) == 1 else None

    @classmethod
    def _pod_matches_scope(
        cls,
        pod: Dict[str, Any],
        scope: tuple[str, str],
    ) -> bool:
        namespace, name = scope
        return (
            cls._pick_text(pod.get("namespace")).lower() == namespace
            and cls._pick_text(pod.get("name")).lower() == name
        )

    @classmethod
    def _scope_abnormal_summary_to_pod(
        cls,
        summary: Dict[str, Any],
        scope: tuple[str, str],
    ) -> Dict[str, Any]:
        scoped = dict(summary or {})
        namespace, name = scope
        selected_rows = []
        status_counts: Dict[str, int] = {}
        for row in scoped.get("selected_rows") or []:
            parts = str(row).split()
            if len(parts) < 4:
                continue
            if parts[0].lower() != namespace or parts[1].lower() != name:
                continue
            selected_rows.append(str(row))
            status = parts[3]
            status_counts[status] = status_counts.get(status, 0) + 1
        scoped["selected_rows"] = selected_rows
        scoped["status_counts"] = status_counts
        scoped["total_abnormal"] = len(selected_rows)
        return scoped

    def _guard_healthy_with_active_abnormalities(
        self,
        layer_result: Dict[str, Any],
        layer_handoff: Dict[str, Any],
        layer: Layer,
        layers: List[Layer],
    ) -> tuple[Layer, List[Layer]]:
        """Reject HEALTHY when current real tool output contains active abnormalities."""
        if layer != Layer.HEALTHY:
            return layer, layers
        if not self._handoff_has_active_abnormalities(layer_handoff):
            return layer, layers

        # 层级映射已移除：存在活跃异常时统一修正为 ABNORMAL
        corrected_layers = [Layer.ABNORMAL]

        corrected_layer = corrected_layers[0]
        corrected_layer_values = [item.value for item in corrected_layers]
        reason_suffix = (
            "系统确定性保护：当前真实 kubectl 工具结果仍包含异常对象，"
            f"拒绝将 layer 输出为 HEALTHY，修正为 {corrected_layer.value}。"
        )
        original_reason = self._pick_text(layer_result.get("reasoning"))

        layer_result["layer"] = corrected_layer.value
        layer_result["derived_layer"] = corrected_layer.value
        layer_result["layers"] = corrected_layer_values
        layer_result["confidence"] = max(float(layer_result.get("confidence") or 0.0), 0.8)
        layer_result["reasoning"] = f"{original_reason}\n{reason_suffix}".strip()

        layer_handoff["layer"] = corrected_layer.value
        layer_handoff["derived_layer"] = corrected_layer.value
        layer_handoff["layers"] = corrected_layer_values
        layer_handoff["confidence"] = layer_result["confidence"]
        layer_handoff["primary_problem"] = layer_result["reasoning"]

        logger.warning(
            "⚠️ [layer] HEALTHY misclassification corrected from real abnormal tool output | corrected_layer=%s issue_groups=%d total_abnormal=%s",
            corrected_layer.value,
            len(layer_handoff.get("issue_groups") or []),
            (layer_handoff.get("current_abnormal_summary") or {}).get("total_abnormal"),
        )
        return corrected_layer, corrected_layers

    @staticmethod
    def _handoff_has_active_abnormalities(layer_handoff: Dict[str, Any]) -> bool:
        """只依据确定性扫描信号判定，LLM 手写字段（abnormal_pods/issue_groups）
        不得作为推翻 HEALTHY 的依据：LLM 可能把历史重启等"值得留意"的对象
        误填进异常字段，而真实表格解析（total_abnormal/selected_rows）已经
        包含 RecentRestart/NotReady 等全部当前异常。"""
        summary = layer_handoff.get("current_abnormal_summary") or {}
        try:
            if int(summary.get("total_abnormal") or 0) > 0:
                return True
        except (TypeError, ValueError):
            pass
        return bool(summary.get("selected_rows"))

    @classmethod
    def _merge_current_abnormal_pods(
        cls,
        llm_pods: List[Dict[str, Any]],
        current_pods: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Merge LLM-selected Pods with current scan facts.

        The LLM may omit secondary anomalies or keep stale historical Pods.
        Current tool scan output is the factual source for active abnormal Pods,
        so scan-only Pods must be preserved and LLM-only Pods are discarded.
        For the same namespace/name, current scan status overrides stale values.
        """
        merged: Dict[tuple[str, str], Dict[str, Any]] = {}
        order: List[tuple[str, str]] = []

        def add_pod(pod: Dict[str, Any], *, prefer_existing: bool = False) -> None:
            name = cls._pick_text(pod.get("name"))
            if not name:
                return
            namespace = cls._pick_text(pod.get("namespace"))
            key = (namespace, name)
            if key not in merged:
                order.append(key)
                merged[key] = {}
            if prefer_existing:
                merged[key] = {**pod, **merged[key]}
            else:
                merged[key] = {**merged[key], **pod}

        for pod in current_pods or []:
            add_pod(pod)
        for pod in llm_pods or []:
            key = (cls._pick_text(pod.get("namespace")), cls._pick_text(pod.get("name")))
            if key in merged:
                add_pod(pod, prefer_existing=True)

        return [merged[key] for key in order if merged.get(key)]

    @classmethod
    def _build_issue_groups(
        cls,
        abnormal_pods: List[Dict[str, Any]],
        default_pod_abnormal_type: str,
        layer_result: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Group current abnormal Pods by normalized status family.

        This is generic handoff structure, not a diagnostic decision tree. It
        preserves all active anomaly families so downstream nodes do not lose
        secondary issues when a single representative object is selected.
        """
        if not abnormal_pods:
            return []

        grouped: Dict[str, Dict[str, Any]] = {}

        for pod in abnormal_pods:
            name = cls._pick_text(pod.get("name"))
            if not name:
                continue
            namespace = cls._pick_text(pod.get("namespace"))
            status = cls._pick_text(pod.get("status"), layer_result.get("pod_status_keyword"))
            status_family = cls._normalize_status_family(status)
            group = grouped.setdefault(
                status_family,
                {
                    "status_keywords": [],
                    "entities": [],
                },
            )
            if status and status not in group["status_keywords"]:
                group["status_keywords"].append(status)
            group["entities"].append({
                "kind": "Pod",
                "namespace": namespace,
                "name": name,
            })

        if not grouped:
            return []

        groups: List[Dict[str, Any]] = []
        for index, (status_family, group) in enumerate(grouped.items(), start=1):
            statuses = group["status_keywords"] or [status_family]
            pod_abnormal_type = cls._derive_group_abnormal_type(
                statuses=statuses,
                default_pod_abnormal_type=default_pod_abnormal_type,
                layer_result=layer_result,
            )
            entities = group["entities"]
            groups.append({
                "group_id": f"g{index}",
                "status_keywords": statuses,
                "pod_abnormal_type": pod_abnormal_type,
                "compatible_layers": [],
                "entities": entities,
                "evidence_plan": [],
                "possible_scenarios": cls._default_scenarios_for_abnormal_type(pod_abnormal_type),
            })

        for index, group in enumerate(groups, start=1):
            group["group_id"] = f"g{index}"
        return groups

    @staticmethod
    def _default_scenarios_for_abnormal_type(pod_abnormal_type: str) -> List[Dict[str, str]]:
        mapping = {
            "ImagePullFailed": [
                {"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"},
                {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"},
                {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"},
            ],
            "TerminatingStuck": [
                {"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"},
                {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"},
                {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"},
            ],
            "OOMKilled": [
                {"scenario": "容器内存限制过低", "probability": "中", "reason": "需验证 Last State/ExitCode/resources"},
                {"scenario": "应用内存使用异常", "probability": "中", "reason": "需验证日志和重启历史"},
            ],
            "CrashLoopBackOffRuntime": [
                {"scenario": "容器启动命令或进程异常退出", "probability": "中", "reason": "需验证 describe/logs/exitCode"},
                {"scenario": "应用启动依赖或配置异常", "probability": "中", "reason": "需验证日志和环境配置"},
            ],
            "PendingUnschedulable": [
                {"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"},
                {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"},
                {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"},
            ],
            "Evicted": [
                {"scenario": "节点资源压力驱逐", "probability": "中", "reason": "需验证 eviction message 和 Node pressure"},
            ],
            "VolumeMountFailed": [
                {"scenario": "Secret/ConfigMap volume 引用缺失", "probability": "中", "reason": "先验证 FailedMount 事件原文和 Pod spec volumes；命中 not found 后不要泛化查 PVC"},
                {"scenario": "PVC/PV/StorageClass 绑定或亲和性异常", "probability": "中", "reason": "仅当 Events/spec 指向 PVC/PV 时验证 PVC/PV/StorageClass"},
                {"scenario": "CSI/NFS/hostPath 挂载链路异常", "probability": "中", "reason": "仅当 Events 指向 timeout/access denied/hostPath/CSI 时扩展"},
            ],
            "ConfigError": [
                {"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"},
            ],
            "NotReadyProbeFailed": [
                {"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"},
            ],
        }
        return mapping.get(pod_abnormal_type, [
            {"scenario": f"{pod_abnormal_type or 'Unknown'} 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}
        ])

    @classmethod
    def _normalize_status_family(cls, status: str) -> str:
        status_text = cls._pick_text(status)
        if status_text in {"ImagePullBackOff", "ErrImagePull", "ImageInspectError"}:
            return "ImagePullFailed"
        return status_text or "Unknown"

    @classmethod
    def _derive_group_abnormal_type(
        cls,
        statuses: List[str],
        default_pod_abnormal_type: str,
        layer_result: Dict[str, Any],
    ) -> str:
        status_set = set(statuses or [])
        if status_set & {"ImagePullBackOff", "ErrImagePull", "ImageInspectError"}:
            return "ImagePullFailed"
        if "Terminating" in status_set:
            return "TerminatingStuck"
        if "CrashLoopBackOff" in status_set:
            return cls._pick_text(default_pod_abnormal_type, "CrashLoopBackOffRuntime")
        if "RecentRestart" in status_set:
            return "CrashLoopBackOffRuntime"
        if "Evicted" in status_set:
            return "Evicted"
        if "Pending" in status_set:
            return "PendingUnschedulable"
        if "Running" in status_set:
            return cls._pick_text(default_pod_abnormal_type, "NotReadyProbeFailed")
        if len(statuses or []) == 1:
            return statuses[0]
        return cls._pick_text(default_pod_abnormal_type, layer_result.get("pod_abnormal_type"), "Unknown")

    @classmethod
    def _extract_current_abnormal_pods_from_events(cls, thinking_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract active abnormal Pods from the current `kubectl get pods -A` table summary."""
        pods: List[Dict[str, Any]] = []
        seen = set()
        for ev in thinking_events or []:
            if ev.get("type") != "tool_result" or ev.get("status") != "success":
                continue
            if ev.get("tool_name") != "kubectl_get_by_kind_in_cluster":
                continue
            structured = ev.get("structured") or {}
            header = str(structured.get("header", ""))
            if not re.search(r"\bREADY\b.*\bSTATUS\b", header):
                continue
            recent_restart_rows = {
                str(row)
                for row in (structured.get("recent_restart_rows") or [])
            }
            for row in structured.get("selected_rows") or []:
                row_text = str(row)
                parts = row_text.split()
                if len(parts) < 4:
                    continue
                namespace, name, ready, status = parts[0], parts[1], parts[2], parts[3]
                is_recent_restart = row_text in recent_restart_rows
                ready_incomplete = False
                if "/" in ready:
                    current, desired = ready.split("/", 1)
                    ready_incomplete = (
                        current.isdigit()
                        and desired.isdigit()
                        and current != desired
                    )
                if is_recent_restart:
                    status = "RecentRestart"
                elif status.lower() in {"completed", "succeeded"}:
                    continue
                elif ready_incomplete and status.lower() == "running":
                    # readiness 探针失败：STATUS 仍是 Running 但 READY 0/1，
                    # 必须保留为异常并显式表达真实信号
                    status = "NotReady"
                elif cls._is_normal_resource_status(status):
                    continue
                key = (namespace, name)
                if key in seen:
                    continue
                seen.add(key)
                pods.append({"name": name, "namespace": namespace, "status": status})
        return pods

    @classmethod
    def _extract_current_abnormal_summary_from_events(cls, thinking_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract structured abnormal status facts from current table outputs."""
        for ev in thinking_events or []:
            if ev.get("type") != "tool_result" or ev.get("status") != "success":
                continue
            if ev.get("tool_name") != "kubectl_get_by_kind_in_cluster":
                continue
            structured = ev.get("structured") or {}
            header = str(structured.get("header", ""))
            if not re.search(r"\bREADY\b.*\bSTATUS\b", header):
                continue

            recent_restart_rows = {
                str(row)
                for row in (structured.get("recent_restart_rows") or [])
            }
            status_counts = {}
            for status, count in (structured.get("status_counts") or {}).items():
                status_text = cls._pick_text(status)
                if not status_text or cls._is_normal_resource_status(status_text):
                    continue
                try:
                    status_counts[status_text] = int(count)
                except (TypeError, ValueError):
                    status_counts[status_text] = count

            selected_rows = []
            for row in structured.get("selected_rows") or []:
                row_text = str(row)
                parts = row_text.split()
                if len(parts) < 4:
                    continue
                ready, status = parts[2], parts[3]
                ready_incomplete = False
                if "/" in ready:
                    current, desired = ready.split("/", 1)
                    ready_incomplete = (
                        current.isdigit()
                        and desired.isdigit()
                        and current != desired
                    )
                if row_text in recent_restart_rows:
                    status = "RecentRestart"
                elif status.lower() in {"completed", "succeeded"}:
                    continue
                elif ready_incomplete and status.lower() == "running":
                    status = "NotReady"
                elif cls._is_normal_resource_status(status):
                    continue
                selected_rows.append(row_text)
                if status == "RecentRestart" or not structured.get("status_counts"):
                    status_counts[status] = status_counts.get(status, 0) + 1

            return {
                "source": ev.get("tool_name", "kubectl_get_by_kind_in_cluster"),
                "status_counts": status_counts,
                "total_abnormal": sum(v for v in status_counts.values() if isinstance(v, int)) or len(selected_rows),
                "selected_rows": selected_rows[:20],
                "raw_ref": ev.get("raw_ref"),
                "structured_ref": ev.get("structured_ref"),
                "summary_ref": ev.get("summary_ref"),
            }
        return {
            "source": "",
            "status_counts": {},
            "total_abnormal": 0,
            "selected_rows": [],
        }

    @staticmethod
    def _is_normal_resource_status(status: str) -> bool:
        return str(status or "").strip().lower() in {
            "running",
            "completed",
            "succeeded",
            "ready",
            "bound",
            "active",
        }

    @staticmethod
    def _normalize_entities(entities: Any) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        current_namespace = ""
        if not isinstance(entities, list):
            return normalized
        for entity in entities:
            if isinstance(entity, dict):
                etype = entity.get("type", "")
                value = entity.get("value") or entity.get("name") or ""
                namespace = entity.get("namespace", "")
                item = {"type": etype, "name": value}
                if namespace:
                    item["namespace"] = namespace
                normalized.append(item)
                if etype.lower() == "namespace" and value:
                    current_namespace = value
            else:
                normalized.append({"type": "Unknown", "name": str(entity)})
        if current_namespace:
            for item in normalized:
                if item.get("type", "").lower() != "namespace" and "namespace" not in item:
                    item["namespace"] = current_namespace
        return normalized

    @classmethod
    def _normalize_abnormal_pods(
        cls,
        abnormal_pods: Any,
        active_entities: List[Dict[str, Any]],
        fallback_status: Any,
    ) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        fallback_status_text = cls._pick_text(fallback_status)
        if isinstance(abnormal_pods, list):
            for pod in abnormal_pods:
                normalized_pod = cls._normalize_pod_ref(pod)
                if not normalized_pod:
                    continue
                if isinstance(pod, dict):
                    status = cls._pick_text(
                        pod.get("status"),
                        pod.get("reason"),
                        fallback_status_text,
                    )
                    if status:
                        normalized_pod["status"] = status
                elif fallback_status_text:
                    normalized_pod["status"] = fallback_status_text
                normalized.append(normalized_pod)

        if normalized:
            return normalized

        for entity in active_entities:
            if str(entity.get("type", "")).lower() != "pod" or not entity.get("name"):
                continue
            item = {
                "name": entity.get("name", ""),
                "namespace": entity.get("namespace", ""),
            }
            if fallback_status_text:
                item["status"] = fallback_status_text
            normalized.append(item)
        return normalized

    @classmethod
    def _normalize_pod_ref(cls, pod: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(pod, dict):
            return None
        name = cls._pick_text(pod.get("name"), pod.get("value"))
        if not name:
            return None
        normalized = {"name": name}
        namespace = cls._pick_text(pod.get("namespace"))
        if namespace:
            normalized["namespace"] = namespace
        return normalized

    @classmethod
    def _derive_pod_abnormal_type(cls, layer_result: Dict[str, Any]) -> str:
        direct_value = cls._pick_text(layer_result.get("pod_abnormal_type"))
        if direct_value:
            return direct_value

        scenarios = layer_result.get("possible_scenarios")
        if isinstance(scenarios, list):
            for item in scenarios:
                if isinstance(item, dict):
                    value = cls._pick_text(item.get("scenario"), item.get("type"))
                    if value:
                        return value
                elif isinstance(item, str) and item.strip():
                    return item.strip()

        return cls._pick_text(layer_result.get("pod_status_keyword"))

    @classmethod
    def _derive_status_category(cls, layer_result: Dict[str, Any], pod_abnormal_type: str) -> str:
        direct_value = cls._pick_text(layer_result.get("status_category"))
        if direct_value:
            return direct_value

        mapping = {
            "Evicted": "node_pressure",
            "VolumeMountFailed": "storage_volume",
            "PendingUnschedulable": "scheduling",
            "NodeLostOrUnknown": "node_kubelet",
            "TerminatingStuck": "lifecycle",
            "OOMKilled": "container_resource",
            "CrashLoopBackOffRuntime": "container_runtime",
            "ImagePullFailed": "image_registry",
            "SandboxCreateFailed": "network_cni_runtime",
            "ConfigError": "app_config",
            "NotReadyProbeFailed": "app_health",
        }
        return mapping.get(pod_abnormal_type, "")

    @staticmethod
    def _pick_text(*values: Any) -> str:
        for value in values:
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    @staticmethod
    def _compact_signal(text: str, limit: int = 500) -> str:
        compact = " ".join((text or "").split())
        return compact[:limit] + ("..." if len(compact) > limit else "")

    @staticmethod
    def _extract_runbook_id(event: Dict[str, Any]) -> str:
        tool_args = event.get("tool_args") or {}
        if isinstance(tool_args, dict):
            runbook_id = str(tool_args.get("runbook_id") or "").strip()
            if runbook_id:
                return runbook_id
        structured = event.get("structured") or {}
        if isinstance(structured, dict):
            runbook_id = str(structured.get("runbook_id") or structured.get("runbook_name") or "").strip()
            if runbook_id:
                return runbook_id
        raw = (event.get("result", "") or event.get("result_preview", "") or "")
        match = re.search(r"\[([a-z0-9][a-z0-9-]+)\]|runbook_id[:=]\s*([a-z0-9-]+)", raw, re.IGNORECASE)
        if match:
            return match.group(1) or match.group(2) or ""
        return ""

    def _analyze_with_llm(self, question: str) -> tuple:
        """使用 LLM 分析 Pod 异常状态。

        正常路径: AICall agent 只负责工具调用和事实采集；
        layer_extract 使用非流式 Pydantic structured call 从已有工具结果生成
        LayerOutput。避免在 streaming 多工具 agent 中混用 response_format。

        Returns:
            (layer_result_dict, intermediate_events_list)
        """
        thinking_events = []
        try:
            # ── 阶段1：工具调用，收集集群状态 ──
            logger.info("📍 [layer] 阶段1: AICall 工具调用开始 | tools=%d",
                        len(getattr(self, 'tools', [])))
            early_stop_enabled = self._is_early_stop_enabled(default=True)
            explicit_pod_early_stop_enabled = self._is_explicit_pod_early_stop_enabled(
                default=True
            )
            logger.info(
                "🧭 [layer] early_stop=%s explicit_pod_early_stop=%s",
                early_stop_enabled,
                explicit_pod_early_stop_enabled,
            )
            if self._is_direct_query_mode() and early_stop_enabled:
                stop_checker = self._should_stop_query_direct_early
            elif explicit_pod_early_stop_enabled:
                stop_checker = lambda events: self._should_stop_explicit_pod_early(
                    question,
                    events,
                )
            else:
                stop_checker = None
            response, thinking_events = self._call_llm(
                question,
                self._get_layer_prompt(),
                expect_json=self._is_direct_query_mode(),
                json_validator=(
                    self._is_query_direct_json_result
                    if self._is_direct_query_mode()
                    else None
                ),
                skip_remediation_policy=self._is_direct_query_mode(),
                blocked_tool_names=(
                    self.QUERY_DIRECT_BLOCKED_TOOLS
                    if self._is_direct_query_mode()
                    else self._get_layer_blocked_tool_names()
                ),
                stop_checker=stop_checker,
            )

            stage1_text = (response.result or "") if response else ""
            if not stage1_text:
                logger.warning("⚠️ [layer] 阶段1 无最终文本，仅基于工具结果执行结构化整理")
            else:
                logger.debug("📋 [layer] 阶段1 输出: %s", stage1_text[:200])

            if self._is_llm_unavailable_text(stage1_text) and not self._has_successful_tool_results(thinking_events):
                raise RuntimeError(self._llm_unavailable_message(stage1_text))

            full_analysis_text = self._build_full_analysis(stage1_text, thinking_events)

            # 压缩 enriched_text（可能含大量工具原始输出，50-100K chars）
            # 压缩后传给下游 evidence/rca/conclusion，避免 token overflow
            compact_threshold = 30000
            if len(full_analysis_text) > compact_threshold:
                logger.info("📦 [layer] enriched_text 过大 (%d chars)，执行 LLM 压缩",
                            len(full_analysis_text))
                enriched_text_for_downstream = self._compact_context(
                    full_analysis_text, max_chars=compact_threshold
                )
            else:
                enriched_text_for_downstream = full_analysis_text

            if self._is_direct_query_mode():
                extracted_json = self._try_parse_json(stage1_text)
                extracted_json = self._normalize_layer_output_dict(extracted_json)
                extracted_json = self._normalize_query_result_sources(extracted_json, thinking_events)
                if isinstance(extracted_json, dict):
                    if str(extracted_json.get("layer") or "").upper() != "QUERY":
                        extracted_json["full_analysis"] = enriched_text_for_downstream
                        return extracted_json, thinking_events
                    if self._is_usable_query_result(extracted_json, thinking_events):
                        extracted_json["full_analysis"] = enriched_text_for_downstream
                        logger.info(
                            "✅ [layer] QUERY direct 使用阶段1 JSON 文本结果 | rows=%d sources=%d",
                            len(((extracted_json.get("query_result") or {}).get("rows")) or []),
                            len(((extracted_json.get("query_result") or {}).get("sources")) or []),
                        )
                        return extracted_json, thinking_events

                tool_query_result = self._query_result_from_prometheus_tool_events(question, thinking_events)
                if tool_query_result is not None and self._has_successful_tool_results(thinking_events):
                    result = {
                        "layer": "QUERY",
                        "layers": ["QUERY"],
                        "layer_name": "查询请求",
                        "confidence": 0.8,
                        "reasoning": "已基于真实 Prometheus 工具结果生成 QUERY 结构化结果。",
                        "key_entities": [],
                        "possible_scenarios": [],
                        "query_result": tool_query_result,
                        "full_analysis": enriched_text_for_downstream,
                    }
                    logger.info(
                        "✅ [layer] QUERY direct 跳过 layer_extract，从真实 Prometheus tool_result 构建 LayerOutput | rows=%d sources=%d",
                        len((tool_query_result or {}).get("rows") or []),
                        len((tool_query_result or {}).get("sources") or []),
                    )
                    return result, thinking_events

                failure_reason = "QUERY direct 未获得可渲染 JSON，也未获得任何可用 Prometheus 工具结果"
                logger.warning(
                    "⚠️ [layer] %s | tool_events=%d",
                    failure_reason,
                    len(thinking_events or []),
                )
                return self._build_query_direct_failure_result(
                    question=question,
                    full_analysis_text=enriched_text_for_downstream,
                    failure_reason=failure_reason,
                ), thinking_events

            extracted = self._extract_with_lite_llm(
                question=question,
                full_analysis_text=enriched_text_for_downstream,
                failure_reason="基于 layer 阶段工具结果和分析文本生成 Pydantic LayerOutput",
            )
            extracted = self._normalize_layer_output_dict(extracted)
            extracted = self._normalize_query_result_sources(extracted, thinking_events)
            if extracted is None:
                raise RuntimeError("layer 未能生成 Pydantic LayerOutput")

            if self._is_direct_query_mode() and str(extracted.get("layer") or "").upper() != "QUERY":
                tool_query_result = self._query_result_from_prometheus_tool_events(question, thinking_events)
                if tool_query_result is not None and self._has_successful_tool_results(thinking_events):
                    logger.info(
                        "✅ [layer] QUERY direct 从真实 Prometheus tool_result 构建 QueryResult | rows=%d sources=%d",
                        len(tool_query_result.get("rows") or []),
                        len(tool_query_result.get("sources") or []),
                    )
                    return {
                        "layer": "QUERY",
                        "layers": ["QUERY"],
                        "layer_name": "查询请求",
                        "confidence": max(float(extracted.get("confidence") or 0.0), 0.8),
                        "reasoning": "已基于真实 Prometheus 工具结果生成 QUERY 结构化结果。",
                        "key_entities": extracted.get("key_entities") or [],
                        "possible_scenarios": extracted.get("possible_scenarios") or [],
                        "query_result": tool_query_result,
                        "full_analysis": enriched_text_for_downstream,
                    }, thinking_events
                failure_reason = "QUERY 请求未获得任何可用的真实工具结果，拒绝将查询失败误分类为故障诊断层"
                logger.warning(
                    "⚠️ [layer] %s | tool_events=%d prometheus_sources=%d",
                    failure_reason,
                    len(thinking_events or []),
                    len(self._query_sources_from_tool_events(thinking_events)),
                )
                return self._build_query_direct_failure_result(
                    question=question,
                    full_analysis_text=enriched_text_for_downstream,
                    failure_reason=failure_reason,
                ), thinking_events

            if self._is_direct_query_mode() and str(extracted.get("layer") or "").upper() == "QUERY" and not self._is_usable_query_result(extracted, thinking_events):
                tool_query_result = self._query_result_from_prometheus_tool_events(question, thinking_events)
                if tool_query_result is not None:
                    extracted["query_result"] = tool_query_result
                    logger.info(
                        "✅ [layer] QUERY direct Pydantic query_result 缺失，已从 Prometheus tool_result 补齐 | rows=%d sources=%d",
                        len(tool_query_result.get("rows") or []),
                        len(tool_query_result.get("sources") or []),
                    )
                    if self._is_usable_query_result(extracted, thinking_events):
                        extracted["full_analysis"] = enriched_text_for_downstream
                        return extracted, thinking_events

                logger.warning("⚠️ [layer] QUERY direct Pydantic 输出缺少真实工具结果或有效 rows，发起一次严格重试")
                retry_response, retry_events = self._call_llm(
                    question,
                    self._get_query_retry_prompt(),
                    expect_json=False,
                    stop_checker=(
                        self._should_stop_query_direct_early
                        if early_stop_enabled
                        else None
                    ),
                )
                thinking_events = (thinking_events or []) + (retry_events or [])
                retry_text = retry_response.result if retry_response else ""
                full_analysis_text = self._build_full_analysis(retry_text, thinking_events)
                if len(full_analysis_text) > compact_threshold:
                    enriched_text_for_downstream = self._compact_context(
                        full_analysis_text, max_chars=compact_threshold
                    )
                else:
                    enriched_text_for_downstream = full_analysis_text
                retry_result = self._extract_with_lite_llm(
                    question=question,
                    full_analysis_text=enriched_text_for_downstream,
                    failure_reason="基于 QUERY direct 严格重试后的工具结果生成 Pydantic LayerOutput",
                )
                retry_result = self._normalize_layer_output_dict(retry_result)
                retry_result = self._normalize_query_result_sources(retry_result, thinking_events)
                if not self._is_usable_query_result(retry_result, thinking_events):
                    tool_query_result = self._query_result_from_prometheus_tool_events(question, thinking_events)
                    if isinstance(retry_result, dict) and tool_query_result is not None:
                        retry_result["layer"] = "QUERY"
                        retry_result["layers"] = ["QUERY"]
                        retry_result["query_result"] = tool_query_result
                        logger.info(
                            "✅ [layer] QUERY direct retry 后从 Prometheus tool_result 补齐 QueryResult | rows=%d sources=%d",
                            len(tool_query_result.get("rows") or []),
                            len(tool_query_result.get("sources") or []),
                        )
                if self._is_usable_query_result(retry_result, thinking_events):
                    retry_result["full_analysis"] = enriched_text_for_downstream
                    return retry_result, thinking_events

                failure_reason = "QUERY 请求未获得任何可用的真实工具结果，拒绝直接返回伪结构化结果"
                logger.warning(
                    "⚠️ [layer] %s | tool_events=%d prometheus_sources=%d",
                    failure_reason,
                    len(thinking_events or []),
                    len(self._query_sources_from_tool_events(thinking_events)),
                )
                return self._build_query_direct_failure_result(
                    question=question,
                    full_analysis_text=enriched_text_for_downstream,
                    failure_reason=failure_reason,
                ), thinking_events

            logger.info("✅ [layer] Pydantic LayerOutput 完成: layer=%s, confidence=%.2f",
                        extracted.get('layer'), extracted.get('confidence', 0))
            extracted["full_analysis"] = enriched_text_for_downstream
            return extracted, thinking_events

        except Exception as e:
            if self._is_llm_unavailable_text(str(e)):
                raise
            if not self._allow_layer_extract_fallback():
                raise
            logger.warning(f"[layer] LLM 分析失败，转入 Pydantic 提取: {e}")
            full_analysis_text = self._build_full_analysis("", thinking_events)
            extracted = self._extract_with_lite_llm(
                question=question,
                full_analysis_text=full_analysis_text or f"# layer 阶段1异常\n{str(e)}",
                failure_reason=f"LLM 定层失败，转入 Pydantic LayerOutput 提取: {str(e)}",
            )
            if extracted is None:
                raise
            return extracted, thinking_events

    def _extract_with_lite_llm(
        self,
        question: str,
        full_analysis_text: str,
        failure_reason: str = "",
    ) -> Optional[Dict[str, Any]]:
        """基于已收集内容生成唯一 Pydantic LayerOutput。"""
        ai_call = getattr(self, "ai_call", None)
        if ai_call is None or not hasattr(ai_call, "call_structured"):
            logger.warning("⚠️ [layer] ai_call 不支持 call_structured，无法生成 Pydantic LayerOutput")
            return None

        extract_prompt = self._get_layer_extract_prompt()
        extract_input = (
            f"# 用户问题\n{question}\n\n"
            f"# 失败原因\n{failure_reason or '未提供'}\n\n"
            f"# 分析文本\n{full_analysis_text or '无'}"
        )
        llm_start = time.time()
        try:
            structured, raw = ai_call.call_structured(
                system_prompt=extract_prompt,
                question=extract_input,
                schema=LayerOutput,
                node_id="layer_extract",
                run_id=getattr(self, "current_run_id", ""),
                max_tokens=2048,
                allow_text_fallback=True,
            )
        finally:
            if self.metrics:
                self.metrics.record_llm_call(
                    self.node_id,
                    (time.time() - llm_start) * 1000,
                )
        parsed = structured.model_dump(exclude_none=True) if structured is not None else None

        if parsed is None:
            logger.warning("⚠️ [layer] Pydantic 提取未返回合法 LayerOutput | raw=%s", (raw or "")[:500])
            return None

        parsed = self._normalize_layer_output_dict(parsed) or parsed
        parsed["full_analysis"] = full_analysis_text
        logger.info("✅ [layer] lite 提取成功: layer=%s confidence=%.2f",
                    parsed.get("layer"), parsed.get("confidence", 0.0))
        return parsed

    @staticmethod
    def _try_parse_json(text: str) -> Optional[Dict[str, Any]]:
        """Parse first-round model JSON text without requiring structured LLM output."""
        try:
            from app.core.aicall.client import AICall

            parsed = AICall.extract_json_payload(text)
        except Exception:
            return None
        if not isinstance(parsed, dict):
            return None
        return parsed

    @staticmethod
    def _is_structured_layer_result(result: Optional[Dict]) -> bool:
        """判断阶段1输出是否已是可用的结构化定层结果。"""
        try:
            LayerOutput.model_validate(result)
        except Exception:
            return False
        return True

    @staticmethod
    def _is_query_direct_json_result(result: Optional[Dict]) -> bool:
        """Lightweight JSON-text guard for `/query` direct; no structured LLM/Pydantic call."""
        if not isinstance(result, dict):
            return False
        layer = str(result.get("layer") or "").upper()
        if layer not in {"QUERY", "HEALTHY", "ABNORMAL", "L0", "L1", "L2", "L3", "L4"}:
            return False
        if layer == "QUERY":
            query_result = result.get("query_result")
            return isinstance(query_result, dict)
        return True

    @staticmethod
    def _build_full_analysis(llm_text: str, thinking_events: list) -> str:
        """构建阶段1完整分析文本：LLM 输出 + 工具返回的原始数据。"""
        parts = [llm_text]

        tool_data = []
        for ev in thinking_events:
            # 收集工具调用结果
            if ev.get("type") == "tool_result" and ev.get("status") == "success":
                tool_name = ev.get("tool_name", "unknown")
                # 优先用完整结果，回退到 preview
                result_text = ev.get("result", "") or ev.get("result_preview", "")
                if result_text:
                    tool_data.append(f"[{tool_name}]\n{result_text}")

        if tool_data:
            parts.append("\n\n# 工具返回的原始数据（以此为准）")
            parts.extend(tool_data)

        return "\n".join(parts)

    def _analyze_with_rules(self, question: str) -> Dict:
        """无 LLM 时的低置信度兜底分类，避免使用人工关键词规则主导分类。"""
        return {
            "layer": "ABNORMAL",
            "layer_name": "",
            "confidence": 0.1,
            "reasoning": "LLM 不可用，无法完成基于问题和环境的可靠定位，按异常诊断低置信度兜底",
            "key_entities": [],
            "possible_scenarios": []
        }

    def _parse_layer(self, layer_str: str) -> Layer:
        """解析模式判定字符串：HEALTHY / QUERY / 其余（含历史 L0-L4）均为 ABNORMAL。"""
        value = (layer_str or "").strip().upper()
        if value == "HEALTHY":
            return Layer.HEALTHY
        if value == "QUERY":
            return Layer.QUERY
        return Layer.ABNORMAL
