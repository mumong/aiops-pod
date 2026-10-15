"""
工作流节点基类

设计原则：
- 高内聚：每个节点封装完整的业务逻辑
- 低耦合：只依赖状态输入，不依赖其他节点
- 可扩展：新增节点只需继承此类
- 公共 LLM 调用：通过 _call_llm() 统一 streaming + metrics + thinking
"""

import logging
import queue
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Tuple

from app.core.context.archive import ContextArchive
from app.core.context.budget import ContextBudgetEstimator, serialize_tool_schema
from app.core.prompts import (
    REMEDIATION_AUTO_MODE_LINE,
    REMEDIATION_POLICY_TEMPLATE,
    REMEDIATION_REVIEW_MODE_LINE,
    RUNBOOK_CATALOG_INSTRUCTION,
    VISIBLE_OUTPUT_LANGUAGE_POLICY,
)
from app.core.remediation.models import normalize_remediation_mode
from app.core.workflow.state import WorkflowState

logger = logging.getLogger(__name__)


class WorkflowNode(ABC):
    """
    工作流节点基类

    所有工作流节点必须继承此类并实现 execute 方法
    """

    # 实例级事件队列：当不为 None 时，_call_llm 使用 call_with_stream_and_queue
    # 以便 executor 实时读取 thinking 事件（每个请求独立）
    _event_queue: Optional[queue.Queue] = None

    # 取消信号：客户端断开时 executor 会 set()，节点/AICall 检测后提前退出
    cancel_event: Optional[Any] = None

    def set_event_queue(self, q: Optional[queue.Queue]):
        """设置实例级事件队列（executor 在启动 workflow 前调用）"""
        self._event_queue = q

    @property
    @abstractmethod
    def node_id(self) -> str:
        """节点唯一标识"""
        pass

    @property
    @abstractmethod
    def node_name(self) -> str:
        """节点显示名称"""
        pass

    @abstractmethod
    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        执行节点逻辑

        Args:
            state: 当前工作流状态（只读输入）

        Returns:
            更新后的状态（只更新自己负责的字段）

        设计原则：
        - 不修改输入 state，返回新状态
        - 只更新自己负责的字段
        - 异常处理：捕获异常并写入 state.errors
        """
        pass

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
            logger.warning("[%s] 写入 node input archive 失败: %s", self.node_id, exc)

    def _archive_node_output(
        self,
        payload: Any,
        *,
        artifact_name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Atomically archive one named node output and return its digest ref."""
        run_id = getattr(self, "current_run_id", "")
        if not run_id:
            return None
        safe_name = artifact_name or f"{self.node_id}.output"
        try:
            return ContextArchive(run_id=run_id).write_json_atomic(
                f"node_outputs/{safe_name}.json",
                payload,
            )
        except Exception as exc:
            logger.warning(
                "[%s] 写入 node output archive 失败: %s",
                self.node_id,
                exc,
            )
            return None

    def _get_workflow_config(self) -> dict:
        """Return workflow config visible to this node.

        Tests and executor can set workflow_config_override directly on the node.
        Production nodes read the initialized HolmesService workflow_config.
        """
        override = getattr(self, "workflow_config_override", None)
        if isinstance(override, dict):
            return override
        service = getattr(self, "holmes_service", None)
        config = getattr(service, "workflow_config", {}) if service is not None else {}
        return config if isinstance(config, dict) else {}

    @staticmethod
    def _parse_bool_config(value: Any, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "y", "on"}:
            return True
        if text in {"0", "false", "no", "n", "off"}:
            return False
        return default

    def _is_structured_runtime_fallback_enabled(self, default: bool = True) -> bool:
        wf_config = self._get_workflow_config()
        runtime_cfg = (
            wf_config.get("structured_runtime", {}) if isinstance(wf_config, dict) else {}
        )
        if isinstance(runtime_cfg, dict) and "fallback_enabled" in runtime_cfg:
            return self._parse_bool_config(runtime_cfg.get("fallback_enabled"), default)
        return default

    def should_inject_runbook_catalog(self) -> bool:
        """节点是否需要在 prompt 中注入 runbook catalog。"""
        return True

    def _call_llm(
        self,
        question: str,
        system_prompt: str,
        stop_checker: Optional[Callable[[list], bool]] = None,
        **kwargs,
    ) -> Tuple[Any, list]:
        """
        公共 LLM 调用 — 通过 AICall (LangChain create_agent) 执行

        Args:
            question: 用户问题
            system_prompt: 节点专用 system prompt

        Returns:
            (AICallResult, thinking_events)
        """
        ai_call = getattr(self, "ai_call", None)
        if ai_call is None:
            raise RuntimeError(
                f"[{self.node_id}] ai_call 未设置，无法调用 LLM。"
                "请确保 USE_AICALL=true 且 AICall 初始化成功。"
            )

        start_time = time.time()
        force_no_tools = bool(kwargs.pop("force_no_tools", False))
        skip_remediation_policy = bool(kwargs.pop("skip_remediation_policy", False))
        blocked_tool_names = {
            str(item) for item in (kwargs.pop("blocked_tool_names", []) or []) if str(item).strip()
        }
        max_steps = 10
        if getattr(self, "holmes_service", None):
            max_steps = self.holmes_service.get_node_max_steps(self.node_id)

        prompt_components = []

        # Inject runbook catalog into system_prompt
        catalog_text = ""
        if (
            self.should_inject_runbook_catalog()
            and getattr(self, "runbook_catalog", None)
            and hasattr(self.runbook_catalog, "catalog")
        ):
            entries = self.runbook_catalog.catalog
            if entries:
                lines = ["# Available Runbooks", RUNBOOK_CATALOG_INSTRUCTION, ""]
                for e in entries:
                    desc = getattr(e, "description", "") or ""
                    link = getattr(e, "link", "") or ""
                    lines.append(f"- {link}: {desc}")
                catalog_text = "\n".join(lines)
                logger.debug("[%s] 注入 %d 条 Runbook 到 prompt", self.node_id, len(entries))

        if catalog_text:
            prompt_components.append(
                {
                    "name": "runbook_catalog",
                    "category": "static_input",
                    "content": catalog_text,
                }
            )
        prompt_components.append(
            {
                "name": "node_system_prompt",
                "category": "static_input",
                "content": system_prompt,
            }
        )

        full_prompt = system_prompt
        if catalog_text:
            full_prompt = catalog_text + "\n\n" + system_prompt

        if not skip_remediation_policy:
            wf_config = self._get_workflow_config()
            remediation_cfg = (
                wf_config.get("remediation", {}) if isinstance(wf_config, dict) else {}
            )
            remediation_mode = "review"
            if isinstance(remediation_cfg, dict):
                remediation_mode = normalize_remediation_mode(remediation_cfg.get("mode"))
            if remediation_mode == "auto":
                mode_line = REMEDIATION_AUTO_MODE_LINE
            else:
                mode_line = REMEDIATION_REVIEW_MODE_LINE
            remediation_policy = REMEDIATION_POLICY_TEMPLATE.format(mode_line=mode_line)
            full_prompt += remediation_policy
            prompt_components.append(
                {
                    "name": "remediation_policy",
                    "category": "static_input",
                    "content": remediation_policy,
                }
            )

        language_policy = VISIBLE_OUTPUT_LANGUAGE_POLICY
        full_prompt += language_policy
        prompt_components.append(
            {
                "name": "language_policy",
                "category": "static_input",
                "content": language_policy,
            }
        )

        tools = [] if force_no_tools else (getattr(self, "tools", []) or [])
        if blocked_tool_names:
            tools = [
                tool
                for tool in tools
                if str(getattr(tool, "name", "") or "") not in blocked_tool_names
            ]
        run_id = getattr(self, "current_run_id", "") or kwargs.pop("run_id", "")
        tool_schema_payload = serialize_tool_schema(tools)
        static_context_components = [
            *prompt_components,
            {
                "name": "user_message",
                "category": "static_input",
                "content": question,
            },
            {
                "name": "tool_schema",
                "category": "static_input",
                "content": tool_schema_payload,
                "preview": ",".join(
                    str(item.get("name", "")) for item in tool_schema_payload[:20]
                ),
            },
            {
                "name": "scratchpad_reserved",
                "category": "reserved",
                "tokens": 4096,
                "preview": "reserved for reasoning/tool calls",
            },
            {
                "name": "output_reserved",
                "category": "reserved",
                "tokens": 6000,
                "preview": "reserved for model output",
            },
        ]
        budget = ContextBudgetEstimator().estimate(
            node_id=self.node_id,
            model=getattr(ai_call, "model_str", getattr(ai_call, "model", "")),
            system_prompt=full_prompt,
            user_message=question,
            tools=tools,
            handoff=kwargs.pop("handoff_for_budget", None),
            components=static_context_components,
            api_base=getattr(ai_call, "api_base", "") or "",
            api_key=getattr(ai_call, "api_key", "") or "",
            enable_usage_probe=False,
        )
        ContextBudgetEstimator().log(budget)
        if run_id:
            try:
                ContextArchive(run_id=run_id).write_budget(self.node_id, budget)
            except Exception as exc:
                logger.warning("[%s] 写入 context budget 失败: %s", self.node_id, exc)

        logger.info(
            "[%s] AICall.call() 开始 | max_steps=%d tools=%d", self.node_id, max_steps, len(tools)
        )
        logger.debug(
            "[%s] AICall.call() prompt长度=%d字 question长度=%d字",
            self.node_id,
            len(full_prompt),
            len(question),
        )

        result, thinking_events = self.ai_call.call(
            system_prompt=full_prompt,
            question=question,
            tools=tools,
            max_steps=max_steps,
            stream_queue=self._event_queue,
            node_id=self.node_id,
            run_id=run_id,
            cancel_event=self.cancel_event,
            stop_checker=stop_checker,
            static_context_components=static_context_components,
            **kwargs,
        )
        if self._should_retry_without_agent_response_schema(
            result=result,
            thinking_events=thinking_events,
            response_schema=kwargs.get("response_schema"),
            force_no_tools=force_no_tools,
        ):
            logger.warning(
                "[%s] agent response_format 与当前模型网关不兼容，保留 Pydantic fallback，重试无 response_schema 工具采集",
                self.node_id,
            )
            retry_kwargs = dict(kwargs)
            retry_kwargs.pop("response_schema", None)
            result, thinking_events = self.ai_call.call(
                system_prompt=full_prompt,
                question=question,
                tools=tools,
                max_steps=max_steps,
                stream_queue=self._event_queue,
                node_id=self.node_id,
                run_id=run_id,
                cancel_event=self.cancel_event,
                stop_checker=stop_checker,
                static_context_components=static_context_components,
                **retry_kwargs,
            )

        llm_duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "[%s] AICall.call() 完成 | %.1fs | iterations=%d | tools=%d | 输出=%d字",
            self.node_id,
            llm_duration_ms / 1000,
            result.iteration_count if hasattr(result, "iteration_count") else 0,
            result.tool_call_count,
            len(result.result or ""),
        )

        # metrics
        if getattr(self, "metrics", None):
            actual_duration = result.duration_ms or llm_duration_ms
            usage_count = len(
                {
                    (
                        event.get("iteration"),
                        event.get("timestamp"),
                        tuple(sorted((event.get("usage") or {}).items())),
                    )
                    for event in (thinking_events or [])
                    if event.get("type") == "ai_usage" and isinstance(event.get("usage"), dict)
                }
            )
            self.metrics.record_llm_call(
                self.node_id,
                actual_duration,
                request_count=max(1, usage_count),
                source="agent",
            )

        return result, thinking_events

    def _should_retry_without_agent_response_schema(
        self,
        result: Any,
        thinking_events: list,
        response_schema: Optional[type],
        force_no_tools: bool,
    ) -> bool:
        """Detect OpenAI-compatible gateways that reject LangChain ToolStrategy.

        The retry only removes agent response_format. Nodes still use Pydantic
        fallback extraction/validation from the real tool transcript, so this is
        a transport compatibility fallback, not a return to prompt JSON.
        """
        if response_schema is None or force_no_tools:
            return False
        if not self._is_structured_runtime_fallback_enabled(default=True):
            return False
        if any((ev or {}).get("type") == "tool_result" for ev in (thinking_events or [])):
            return False
        content = str(getattr(result, "result", "") or "")
        if not content.startswith("Agent 执行异常:"):
            return False
        incompatible_markers = (
            "MidStreamFallbackError",
            "APIConnectionError",
            "Expecting ':' delimiter",
            "tool",
            "response_format",
            "structured",
            "InternalServerError",
            "Error code: 500",
        )
        return any(marker in content for marker in incompatible_markers)
