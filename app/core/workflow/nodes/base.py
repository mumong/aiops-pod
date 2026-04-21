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
        max_steps = 10
        if getattr(self, 'holmes_service', None):
            max_steps = self.holmes_service.get_node_max_steps(self.node_id)

        # Inject runbook catalog into system_prompt
        catalog_text = ""
        if getattr(self, 'runbook_catalog', None) and hasattr(self.runbook_catalog, 'catalog'):
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

        full_prompt = system_prompt
        if catalog_text:
            full_prompt = catalog_text + "\n\n" + system_prompt

        # 注入修复控制指令（AUTO_REMEDIATE 环境变量控制）
        auto_remediate = os.getenv("AUTO_REMEDIATE", "false").lower() in ("true", "1", "yes")
        if not auto_remediate:
            full_prompt += (
                "\n\n# ⛔ 修复操作限制\n"
                "你只负责**诊断和分析**，**禁止执行任何修复操作**。\n"
                "- 禁止执行 kubectl apply/patch/delete/rollout/taint/scale 等写操作\n"
                "- 禁止执行 iptables 修改、文件删除、进程重启等变更操作\n"
                "- 可以在报告中**建议**修复方案，但不要自行执行\n"
                "- Runbook 中的修复步骤仅供参考，不要执行\n"
            )
        else:
            full_prompt += (
                "\n\n# ✅ 修复操作已授权\n"
                "诊断完成后，如果发现明确的问题且修复方案风险可控，"
                "你可以执行修复操作。执行前在输出中说明即将执行的操作和预期效果。\n"
            )

        tools = getattr(self, 'tools', []) or []
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
            cancel_event=self.cancel_event,
            stop_checker=stop_checker,
            **kwargs,
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
