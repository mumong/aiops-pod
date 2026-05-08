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
from typing import Any, Dict, List, Optional

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

    def _get_prompt_language(self) -> str:
        if self.holmes_service and hasattr(self.holmes_service, "get_prompt_language"):
            return self.holmes_service.get_prompt_language()
        return "zh"

    def should_inject_runbook_catalog(self) -> bool:
        # /query direct 模式下只做轻量真实取数，不注入大段 runbook catalog 干扰本地模型工具决策。
        return not self._is_direct_query_mode()

    def _get_query_mode(self) -> str:
        wf_config = getattr(self, "workflow_config_override", None) or {}
        return str(wf_config.get("query_mode", "full")).strip().lower() or "full"

    def _is_direct_query_mode(self) -> bool:
        return self._get_query_mode() == "direct"

    def _get_layer_prompt(self) -> str:
        if self._is_direct_query_mode():
            return get_workflow_prompt("layer_query_direct", prompt_language=self._get_prompt_language())
        return get_workflow_prompt("layer", prompt_language=self._get_prompt_language())

    def _get_layer_extract_prompt(self) -> str:
        if self._is_direct_query_mode():
            return get_workflow_prompt("layer_query_direct_extract", prompt_language=self._get_prompt_language())
        return get_workflow_prompt("layer_extract", prompt_language=self._get_prompt_language())

    @staticmethod
    def _has_successful_tool_results(thinking_events: List[Dict[str, Any]]) -> bool:
        return any(
            ev.get("type") == "tool_result" and ev.get("status") == "success"
            for ev in (thinking_events or [])
        )

    def _is_usable_query_result(
        self,
        result: Optional[Dict[str, Any]],
        thinking_events: List[Dict[str, Any]],
    ) -> bool:
        if not self._is_structured_layer_result(result):
            return False

        if result.get("layer") != "QUERY":
            return True

        query_result = result.get("query_result")
        if not isinstance(query_result, dict):
            return False

        if not self._has_successful_tool_results(thinking_events):
            return False

        rows = query_result.get("rows", []) or []
        missing = query_result.get("missing", []) or []
        sources = query_result.get("sources", []) or []
        return bool(sources) and bool(rows or missing)

    def _get_query_retry_prompt(self) -> str:
        return (
            self._get_layer_prompt()
            + "\n\n# 上一轮结果被系统拒绝\n"
              "- 原因：你输出了 QUERY JSON，但没有提供足够的真实工具执行结果。\n"
              "- 本轮必须先执行工具，再输出最终 JSON。\n"
              "- 在出现至少一次成功的 tool_result 之前，禁止输出最终答案。\n"
              "- 你的最后一条消息必须建立在真实工具结果之上，而不是工具计划之上。\n"
              "- 如果没有至少一次成功的 tool_result，系统会再次拒绝你的输出。\n"
              "- `query_result.rows` 为空且 `missing` 也为空，视为无效结果。\n"
              "- `collection_summary`、`sources`、`rows` 只能基于真实工具结果填写，禁止编造“已采集 100%”。\n"
        )

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
            layer = self._parse_layer(layer_result.get("layer", "L2"))

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
            "primary_pod": layer_handoff.get("primary_pod"),
            "abnormal_pods": layer_handoff.get("abnormal_pods", []),
            "pod_status_keyword": layer_handoff.get("pod_status_keyword"),
            "pod_abnormal_type": layer_handoff.get("pod_abnormal_type"),
            "derived_layer": layer_handoff.get("derived_layer"),
                "status_category": layer_handoff.get("status_category"),
                "key_entities": layer_result.get("key_entities", []),
                "possible_scenarios": layer_result.get("possible_scenarios", []),
            })
            if layer == Layer.QUERY and self._is_direct_query_mode() and isinstance(query_result, dict):
                new_state["query_result"] = QueryResult.model_validate(query_result).model_dump()

            # 存入 thinking_events（带 node 标记）
            self._save_thinking(state, new_state, thinking_events)

            logger.info(f"✅ 问题定位完成: {layer} (置信度: {layer_result.get('confidence', 0):.0%})")

        except Exception as e:
            logger.error(f"问题定位失败: {e}", exc_info=True)
            new_state.setdefault("errors", []).append(
                f"节点 {self.node_id} 执行失败: {str(e)}"
            )
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
                "primary_pod": layer_handoff.get("primary_pod"),
                "abnormal_pods": layer_handoff.get("abnormal_pods", []),
                "pod_status_keyword": layer_handoff.get("pod_status_keyword"),
                "pod_abnormal_type": layer_handoff.get("pod_abnormal_type"),
                "derived_layer": layer_handoff.get("derived_layer"),
                "status_category": layer_handoff.get("status_category"),
                "key_entities": rescue_result.get("key_entities", []),
                "possible_scenarios": rescue_result.get("possible_scenarios", []),
            })
            if layer == Layer.QUERY and self._is_direct_query_mode() and isinstance(query_result, dict):
                new_state["query_result"] = QueryResult.model_validate(query_result).model_dump()
            self._save_thinking(state, new_state, [])

        return new_state

    @staticmethod
    def _sync_layer_result_from_handoff(layer_result: Dict[str, Any], handoff: Dict[str, Any]) -> None:
        """Keep observable layer_analysis aligned with the factual handoff.

        Pydantic extraction may miss secondary current-state anomalies, while
        handoff merges tool-derived abnormal rows. Persist the merged fields so
        downstream consumers and observability see the same structured facts.
        """
        for key in (
            "abnormal_pods",
            "issue_groups",
            "current_abnormal_summary",
            "pod_status_keyword",
            "pod_abnormal_type",
            "status_category",
        ):
            if key in handoff:
                layer_result[key] = handoff.get(key)

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
        abnormal_pods = self._normalize_abnormal_pods(
            layer_result.get("abnormal_pods"),
            active_entities,
            layer_result.get("pod_status_keyword"),
        )
        current_abnormal_pods = self._extract_current_abnormal_pods_from_events(thinking_events)
        current_abnormal_summary = self._extract_current_abnormal_summary_from_events(thinking_events)
        if current_abnormal_pods:
            abnormal_pods = self._merge_current_abnormal_pods(abnormal_pods, current_abnormal_pods)
        primary_pod = self._normalize_primary_pod(layer_result.get("primary_pod"), abnormal_pods, active_entities)
        if current_abnormal_pods and primary_pod:
            primary_key = (primary_pod.get("namespace", ""), primary_pod.get("name", ""))
            current_keys = {
                (pod.get("namespace", ""), pod.get("name", ""))
                for pod in current_abnormal_pods
                if pod.get("name")
            }
            if primary_key not in current_keys:
                primary_pod = {
                    "name": current_abnormal_pods[0].get("name", ""),
                    "namespace": current_abnormal_pods[0].get("namespace", ""),
                }
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

            signal = ev.get("result", "") or ev.get("result_preview", "")
            if signal:
                active_signals.append({
                    "source": tool_name,
                    "signal": self._compact_signal(signal),
                    "raw_ref": ev.get("raw_ref"),
                    "summary_ref": ev.get("summary_ref"),
                })

        layer_value = layer.value if hasattr(layer, "value") else str(layer)
        pod_abnormal_type = self._derive_pod_abnormal_type(layer_result)
        issue_groups = self._build_issue_groups(
            abnormal_pods=abnormal_pods,
            primary_pod=primary_pod,
            default_pod_abnormal_type=pod_abnormal_type,
            layer_result=layer_result,
        )
        handoff = {
            "diagnosis_scope": "current_state_only" if "之前" in question or "当前" in question or "现在" in question else "question_scope",
            "layer": layer_value,
            "derived_layer": self._pick_text(layer_result.get("derived_layer"), layer_value),
            "layers": [l.value if hasattr(l, "value") else str(l) for l in layers],
            "confidence": layer_result.get("confidence", 0.5),
            "primary_problem": layer_result.get("reasoning", ""),
            "primary_pod": primary_pod,
            "abnormal_pods": abnormal_pods,
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
            "must_verify": [
                "以 issue_groups、abnormal_pods、current_abnormal_summary 为覆盖基准；primary_pod 只是主异常组代表样本",
                "主异常组完整验证，非主异常组最小验证，避免遗漏 Terminating、Pending 等次要异常状态",
                "确认 active_entities 中的对象当前仍存在于指定 namespace",
                "确认 active_signals 仍能被真实工具结果验证",
                "如果工具返回 NotFound、空事件或 namespace 不匹配，记录为冲突/负向证据",
                "如果 primary_pod 不在当前异常 Pod 列表中，必须把它视为历史事件噪音而不是当前故障",
            ],
            "do_not_change": [
                "不要把 primary_pod 替换成其他 Pod，除非真实工具结果证明上游对象不存在或已恢复",
                "不要把上游 namespace、Pod、Service、Node 名称改写成其他对象",
                "不要把历史 event 当成当前故障",
                "不要把计划或工具名当成证据，必须基于 tool_result",
            ],
        }
        return LayerHandoff.model_validate(handoff).model_dump(exclude_none=True)

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
        primary_pod: Optional[Dict[str, Any]],
        default_pod_abnormal_type: str,
        layer_result: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Group current abnormal Pods by normalized status family.

        This is generic handoff structure, not a diagnostic decision tree. It
        preserves all active anomaly families so downstream nodes do not lose
        secondary issues when a single primary_pod is selected.
        """
        if not abnormal_pods:
            return []

        grouped: Dict[str, Dict[str, Any]] = {}
        primary_key = (
            (primary_pod or {}).get("namespace", ""),
            (primary_pod or {}).get("name", ""),
        )

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
                    "primary_entities": [],
                },
            )
            if status and status not in group["status_keywords"]:
                group["status_keywords"].append(status)
            group["primary_entities"].append({
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
            compatible_layer = cls._compatible_layer_for_abnormal_type(pod_abnormal_type)
            entities = group["primary_entities"]
            is_primary = any(
                (entity.get("namespace", ""), entity.get("name", "")) == primary_key
                for entity in entities
            )
            groups.append({
                "group_id": f"g{index}",
                "status_keywords": statuses,
                "pod_abnormal_type": pod_abnormal_type,
                "compatible_layers": [compatible_layer] if compatible_layer else [],
                "primary_entities": entities,
                "is_primary": is_primary,
                "evidence_plan": [],
                "possible_scenarios": cls._default_scenarios_for_abnormal_type(pod_abnormal_type),
            })

        groups.sort(key=lambda item: (not item.get("is_primary"), item.get("group_id", "")))
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
                {"scenario": "PVC/PV/CSI/NFS 挂载失败", "probability": "中", "reason": "需验证 FailedMount 事件和卷对象状态"},
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
    def _compatible_layer_for_abnormal_type(cls, pod_abnormal_type: str) -> str:
        mapping = {
            "Evicted": "L0",
            "VolumeMountFailed": "L0",
            "PendingUnschedulable": "L1",
            "NodeLostOrUnknown": "L1",
            "TerminatingStuck": "L1",
            "OOMKilled": "L2",
            "CrashLoopBackOffRuntime": "L2",
            "ImagePullFailed": "L3",
            "SandboxCreateFailed": "L3",
            "ConfigError": "L4",
            "NotReadyProbeFailed": "L4",
        }
        return mapping.get(pod_abnormal_type, "")

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
            for row in structured.get("selected_rows") or []:
                parts = str(row).split()
                if len(parts) < 4:
                    continue
                namespace, name, ready, status = parts[0], parts[1], parts[2], parts[3]
                if cls._is_normal_resource_status(status):
                    continue
                if "/" in ready:
                    current, desired = ready.split("/", 1)
                    if current == desired and status.lower() == "running":
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
                parts = str(row).split()
                if len(parts) < 4:
                    continue
                status = parts[3]
                if cls._is_normal_resource_status(status):
                    continue
                selected_rows.append(str(row))
                if not structured.get("status_counts"):
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
    def _normalize_primary_pod(
        cls,
        primary_pod: Any,
        abnormal_pods: List[Dict[str, Any]],
        active_entities: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        normalized = cls._normalize_pod_ref(primary_pod)
        if normalized:
            return normalized
        if abnormal_pods:
            return {
                "name": abnormal_pods[0].get("name", ""),
                "namespace": abnormal_pods[0].get("namespace", ""),
            }
        for entity in active_entities:
            if str(entity.get("type", "")).lower() == "pod" and entity.get("name"):
                return {
                    "name": entity.get("name", ""),
                    "namespace": entity.get("namespace", ""),
                }
        return None

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
        raw = (event.get("result", "") or event.get("result_preview", "") or "")
        match = re.search(r"\[([a-z0-9][a-z0-9-]+)\]|runbook_id[:=]\s*([a-z0-9-]+)", raw, re.IGNORECASE)
        if match:
            return match.group(1) or match.group(2) or ""
        return ""

    def _analyze_with_llm(self, question: str) -> tuple:
        """使用 LLM 分析 Pod 异常状态。

        阶段1: AICall agent 调用工具并直接输出 LayerOutput JSON。
        仅当阶段1没有返回合法 LayerOutput 时，才使用无工具 Pydantic
        layer_extract 作为兼容兜底。

        Returns:
            (layer_result_dict, intermediate_events_list)
        """
        thinking_events = []
        try:
            # ── 阶段1：工具调用，收集集群状态 ──
            logger.info("📍 [layer] 阶段1: AICall 工具调用开始 | tools=%d",
                        len(getattr(self, 'tools', [])))
            early_stop_enabled = self._is_early_stop_enabled(default=True)
            logger.info("🧭 [layer] early_stop=%s", early_stop_enabled)
            response, thinking_events = self._call_llm(
                question,
                self._get_layer_prompt(),
                expect_json=early_stop_enabled,
                json_validator=self._is_structured_layer_result,
            )

            stage1_text = (response.result or "") if response else ""
            if not stage1_text:
                logger.warning("⚠️ [layer] 阶段1 无最终文本，仅基于工具结果执行 Pydantic 提取")
            else:
                logger.debug("📋 [layer] 阶段1 输出: %s", stage1_text[:200])

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

            extracted = self._try_parse_json(stage1_text)
            if extracted is None:
                logger.info("📍 [layer] 阶段1未返回合法 LayerOutput，执行 layer_extract 兼容兜底")
                extracted = self._extract_with_lite_llm(
                    question=question,
                    full_analysis_text=enriched_text_for_downstream,
                    failure_reason="基于 layer 阶段工具结果和分析文本生成 Pydantic LayerOutput",
                )
                if extracted is None:
                    raise RuntimeError("layer_extract 未能从现有分析文本中生成 Pydantic LayerOutput")

            if self._is_direct_query_mode() and extracted.get("layer") == "QUERY" and not self._is_usable_query_result(extracted, thinking_events):
                logger.warning("⚠️ [layer] QUERY direct Pydantic 输出缺少真实工具结果或有效 rows，发起一次严格重试")
                retry_response, retry_events = self._call_llm(
                    question,
                    self._get_query_retry_prompt(),
                    expect_json=True,
                    json_validator=self._is_structured_layer_result,
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
                if self._is_usable_query_result(retry_result, thinking_events):
                    retry_result["full_analysis"] = enriched_text_for_downstream
                    return retry_result, thinking_events

                failure_reason = "QUERY 请求未获得任何可用的真实工具结果，拒绝直接返回伪结构化结果"
                logger.warning("⚠️ [layer] %s", failure_reason)
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
        """当 agent 未直接产出合法 JSON 时，基于已收集内容再做一次无工具结构化提取。"""
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
        structured, raw = ai_call.call_structured(
            system_prompt=extract_prompt,
            question=extract_input,
            schema=LayerOutput,
            node_id="layer_extract",
            run_id=getattr(self, "current_run_id", ""),
            max_tokens=2048,
        )
        parsed = structured.model_dump(exclude_none=True) if structured is not None else None

        if parsed is None:
            logger.warning("⚠️ [layer] lite 提取仍未返回合法 JSON | raw=%s", (raw or "")[:500])
            return None

        parsed["full_analysis"] = full_analysis_text
        logger.info("✅ [layer] lite 提取成功: layer=%s confidence=%.2f",
                    parsed.get("layer"), parsed.get("confidence", 0.0))
        return parsed

    @staticmethod
    def _try_parse_json(text: str) -> Optional[Dict]:
        """尝试从文本中提取 JSON，失败返回 None"""
        try:
            from app.core.aicall.client import AICall

            parsed = AICall.extract_json_payload(text)
            if not isinstance(parsed, dict):
                return None
            return LayerOutput.model_validate(parsed).model_dump(exclude_none=True)
        except Exception:
            return None

    @staticmethod
    def _is_structured_layer_result(result: Optional[Dict]) -> bool:
        """判断阶段1输出是否已是可用的结构化定层结果。"""
        try:
            LayerOutput.model_validate(result)
        except Exception:
            return False
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
            "layer": "L2",
            "layer_name": "工作负载层",
            "confidence": 0.1,
            "reasoning": "LLM 不可用，无法完成基于问题和环境的可靠定层，使用低置信度默认层级兜底",
            "key_entities": [],
            "possible_scenarios": []
        }

    def _parse_layer(self, layer_str: str) -> Layer:
        """解析层级字符串为 Layer 枚举"""
        layer_map = {
            "HEALTHY": Layer.HEALTHY,
            "QUERY": Layer.QUERY,
            "L0": Layer.L0,
            "L1": Layer.L1,
            "L2": Layer.L2,
            "L3": Layer.L3,
            "L4": Layer.L4,
        }
        return layer_map.get(layer_str.upper(), Layer.L2)
