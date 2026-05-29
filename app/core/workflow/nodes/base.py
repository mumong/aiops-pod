"""
工作流节点基类

设计原则：
- 高内聚：每个节点封装完整的业务逻辑
- 低耦合：只依赖状态输入，不依赖其他节点
- 可扩展：新增节点只需继承此类
- 公共 LLM 调用：通过 _call_llm() 统一 streaming + metrics + thinking
"""

import logging
import os
import queue
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, List, Optional, Tuple

from app.core.context.archive import ContextArchive
from app.core.context.budget import ContextBudgetEstimator, serialize_tool_schema
from app.core.remediation.models import normalize_remediation_mode
from app.core.workflow.structured_runtime import StructuredAgentRuntime
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

    # 保留类方法兼容旧调用，但标记为 deprecated
    @classmethod
    def set_event_queue_cls(cls, q: queue.Queue):
        """[deprecated] 类级别设置，并发不安全，请用实例方法"""
        pass  # no-op，不再修改类属性

    @classmethod
    def clear_event_queue(cls):
        """[deprecated] 类级别清除，并发不安全"""
        pass  # no-op
    
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
    
    def validate_input(self, state: WorkflowState) -> bool:
        """
        验证输入状态是否满足节点要求（可选）
        
        默认返回 True，子类可重写
        """
        return True
    
    def get_required_fields(self) -> List[str]:
        """
        返回节点执行所需的前置字段（用于依赖检查）

        默认返回空列表，子类可重写
        """
        return []

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

    def _is_early_stop_enabled(self, default: bool = True) -> bool:
        """Whether this node may use its dynamic early-stop mechanism.

        Env override examples:
        - WORKFLOW_LAYER_EARLY_STOP=false
        - WORKFLOW_EVIDENCE_EARLY_STOP=false
        """
        node_key = str(self.node_id or "").upper()
        for env_key in (
            f"WORKFLOW_{node_key}_EARLY_STOP",
            f"AIOPS_WORKFLOW_{node_key}_EARLY_STOP",
        ):
            if env_key in os.environ:
                return self._parse_bool_config(os.getenv(env_key), default)

        wf_config = self._get_workflow_config()
        node_cfg = wf_config.get(self.node_id, {}) if isinstance(wf_config, dict) else {}
        if isinstance(node_cfg, dict):
            early_cfg = node_cfg.get("early_stop", {})
            if isinstance(early_cfg, dict) and "enabled" in early_cfg:
                return self._parse_bool_config(early_cfg.get("enabled"), default)
            if "early_stop_enabled" in node_cfg:
                return self._parse_bool_config(node_cfg.get("early_stop_enabled"), default)

        return default

    def _is_structured_runtime_enabled(self, default: bool = True) -> bool:
        wf_config = self._get_workflow_config()
        runtime_cfg = wf_config.get("structured_runtime", {}) if isinstance(wf_config, dict) else {}
        if isinstance(runtime_cfg, dict):
            nodes = runtime_cfg.get("nodes")
            if isinstance(nodes, dict) and self.node_id in nodes:
                return self._parse_bool_config(nodes.get(self.node_id), default)
            if "enabled" in runtime_cfg:
                return self._parse_bool_config(runtime_cfg.get("enabled"), default)
        return default

    def _is_structured_runtime_fallback_enabled(self, default: bool = True) -> bool:
        wf_config = self._get_workflow_config()
        runtime_cfg = wf_config.get("structured_runtime", {}) if isinstance(wf_config, dict) else {}
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
        ai_call = getattr(self, 'ai_call', None)
        if ai_call is None:
            raise RuntimeError(
                f"[{self.node_id}] ai_call 未设置，无法调用 LLM。"
                "请确保 USE_AICALL=true 且 AICall 初始化成功。"
        )

        start_time = time.time()
        force_no_tools = bool(kwargs.pop("force_no_tools", False))
        max_steps = 10
        if getattr(self, 'holmes_service', None):
            max_steps = self.holmes_service.get_node_max_steps(self.node_id)

        prompt_components = []

        # Inject runbook catalog into system_prompt
        catalog_text = ""
        if self.should_inject_runbook_catalog() and getattr(self, 'runbook_catalog', None) and hasattr(self.runbook_catalog, 'catalog'):
            entries = self.runbook_catalog.catalog
            if entries:
                lines = ["# Available Runbooks",
                         "If one or more runbooks match the issue, use the fetch_runbook tool for each relevant runbook.", ""]
                for e in entries:
                    desc = getattr(e, 'description', '') or ''
                    link = getattr(e, 'link', '') or ''
                    lines.append(f"- {link}: {desc}")
                catalog_text = "\n".join(lines)
                logger.debug("📚 [%s] 注入 %d 条 Runbook 到 prompt", self.node_id, len(entries))

        if catalog_text:
            prompt_components.append({
                "name": "runbook_catalog",
                "category": "static_input",
                "content": catalog_text,
            })
        prompt_components.append({
            "name": "node_system_prompt",
            "category": "static_input",
            "content": system_prompt,
        })

        full_prompt = system_prompt
        if catalog_text:
            full_prompt = catalog_text + "\n\n" + system_prompt

        wf_config = self._get_workflow_config()
        remediation_cfg = wf_config.get("remediation", {}) if isinstance(wf_config, dict) else {}
        remediation_mode = "review"
        if isinstance(remediation_cfg, dict):
            remediation_mode = normalize_remediation_mode(remediation_cfg.get("mode"))
        if remediation_mode == "auto":
            mode_line = "当前修复模式为 auto：结构化修复计划中的安全动作可由修复执行器自动审批并执行。"
        else:
            mode_line = "当前修复模式为 review：结构化修复计划中的所有写动作必须先经过人工审批。"
        remediation_policy = (
            "\n\n# 修复计划与审批约束\n"
            f"- {mode_line}\n"
            "- 诊断节点不要直接执行 kubectl apply/patch/delete/rollout/scale 等写操作。\n"
            "- 如果当前证据确认存在标准、安全、可验证的修复方式，可以在最终报告中生成结构化 remediation_plan actions。\n"
            "- 写动作是否执行由 workflow.remediation.mode 和修复执行器控制；review 模式必须人工审批。\n"
        )
        full_prompt += remediation_policy
        prompt_components.append({
            "name": "remediation_policy",
            "category": "static_input",
            "content": remediation_policy,
        })

        language_policy = (
            "\n\n# 语言与可见输出约束\n"
            "- 全部可见输出必须使用中文，包括分析说明、工具调用前后的说明、结构化字段内的解释文本。\n"
            "- 需要推理时只给结论性、可验证的简短说明，并优先调用工具获取事实。\n"
        )
        full_prompt += language_policy
        prompt_components.append({
            "name": "language_policy",
            "category": "static_input",
            "content": language_policy,
        })

        tools = [] if force_no_tools else (getattr(self, 'tools', []) or [])
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
                "preview": ",".join(str(item.get("name", "")) for item in tool_schema_payload[:20]),
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
        )
        ContextBudgetEstimator().log(budget)
        if run_id:
            try:
                ContextArchive(run_id=run_id).write_budget(self.node_id, budget)
            except Exception as exc:
                logger.warning("⚠️ [%s] 写入 context budget 失败: %s", self.node_id, exc)

        logger.info("📍 [%s] AICall.call() 开始 | max_steps=%d tools=%d",
                     self.node_id, max_steps, len(tools))
        logger.debug("📍 [%s] AICall.call() prompt长度=%d字 question长度=%d字",
                     self.node_id, len(full_prompt), len(question))

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
                "⚠️ [%s] agent response_format 与当前模型网关不兼容，保留 Pydantic fallback，重试无 response_schema 工具采集",
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
        logger.info("✅ [%s] AICall.call() 完成 | %.1fs | iterations=%d | tools=%d | 输出=%d字",
                     self.node_id, llm_duration_ms / 1000,
                     result.iteration_count if hasattr(result, 'iteration_count') else 0,
                     result.tool_call_count, len(result.result or ""))

        # metrics
        if getattr(self, 'metrics', None):
            actual_duration = result.duration_ms or llm_duration_ms
            self.metrics.record_llm_call(self.node_id, actual_duration)
            for _ in range(result.tool_call_count):
                self.metrics.record_tool_call("llm_tool", 0, success=True)

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

    def _call_structured_agent(
        self,
        question: str,
        system_prompt: str,
        schema: type,
        use_tools: bool = True,
        stop_checker: Optional[Callable[[list], bool]] = None,
        **kwargs,
    ) -> Tuple[Any, Any, list]:
        """Finalize a node with a no-tool Pydantic structured call.

        Tool-heavy nodes should collect facts with `_call_llm` first, then use
        this helper for schema finalization. This keeps structured output away
        from streaming multi-tool agent loops, which are fragile on local
        OpenAI-compatible gateways.
        """
        if use_tools:
            response, thinking_events = self._call_llm(
                question,
                system_prompt,
                stop_checker=stop_checker,
                response_schema=schema,
                force_no_tools=False,
                **kwargs,
            )
            parsed = StructuredAgentRuntime.extract_structured_response(response, schema)
            return parsed, response, thinking_events

        ai_call = getattr(self, "ai_call", None)
        if ai_call is None or not hasattr(ai_call, "call_structured"):
            raise RuntimeError(f"[{self.node_id}] ai_call 不支持 call_structured，无法生成结构化输出")

        run_id = getattr(self, "current_run_id", "") or kwargs.pop("run_id", "")
        structured, raw = ai_call.call_structured(
            system_prompt=system_prompt,
            question=question,
            schema=schema,
            node_id=self.node_id,
            run_id=run_id,
            **kwargs,
        )
        from app.core.aicall.types import AICallResult

        response = AICallResult(
            result=raw or "",
            tool_call_count=0,
            iterations=1,
            structured_response=structured,
        )
        events = []
        if structured is not None:
            events.append({
                "type": "structured_response",
                "node": self.node_id,
                "schema": getattr(schema, "__name__", ""),
            })
        return structured, response, events

    def _compact_context(self, text: str, max_chars: int = 30000) -> str:
        """用 LLM 压缩大段上下文，保留关键信息（类似 Claude compact）。

        仅当 text 超过 max_chars 时触发压缩，否则原样返回。
        压缩由 LLM 完成：提取工具调用记录、异常发现、关键实体和数值，
        删除冗余的正常状态数据和重复信息。
        """
        if len(text) <= max_chars:
            return text

        ai_call = getattr(self, 'ai_call', None)
        if ai_call is None:
            logger.warning("📦 [%s] _compact_context: 无 ai_call，硬截断到 %d chars", self.node_id, max_chars)
            return text[:max_chars] + f"\n... (截断，原始 {len(text)} 字符)"

        compress_prompt = (
            "你是一个信息压缩专家。将以下内容压缩为精炼摘要。\n\n"
            "规则：\n"
            "1. 保留所有工具调用记录：工具名 + 关键结果（具体数值、状态、错误信息）\n"
            "2. 保留所有异常发现（Pod 状态异常、错误码、资源超限等）\n"
            "3. 保留关键实体（Pod 名、Node 名、Namespace、IP 地址）\n"
            "4. 删除重复信息和冗余的正常状态数据（如大量 Running 的 Pod 列表只保留异常的）\n"
            "5. 用结构化格式输出，便于下游分析\n"
            "6. 输出必须是中文"
        )

        try:
            logger.info("📦 [%s] 执行 LLM 压缩: %d chars → 目标 %d chars",
                        self.node_id, len(text), max_chars)
            compressed = ai_call.call_simple(
                system_prompt=compress_prompt,
                question=f"请压缩以下内容（原始 {len(text)} 字符，目标 {max_chars} 字符以内）：\n\n{text}",
                max_tokens=4096,
            )
            if compressed and len(compressed) < len(text):
                logger.info("📦 [%s] LLM 压缩完成: %d → %d chars (%.0f%%)",
                            self.node_id, len(text), len(compressed),
                            len(compressed) / len(text) * 100)
                return compressed
        except Exception as e:
            logger.warning("📦 [%s] LLM 压缩失败，硬截断: %s", self.node_id, e)

        return text[:max_chars] + f"\n... (截断，原始 {len(text)} 字符)"

    def _save_thinking(self, state: WorkflowState, new_state: dict, thinking_events: list):
        """将 thinking_events 带 node 标记存入 state"""
        prev = state.get("thinking_events", [])
        new_state["thinking_events"] = prev + [
            {**ev, "node": self.node_id} for ev in thinking_events
        ]
