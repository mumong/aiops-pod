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
from typing import Any, ClassVar, List, Optional, Tuple

from app.core.workflow.state import WorkflowState

logger = logging.getLogger(__name__)


class WorkflowNode(ABC):
    """
    工作流节点基类

    所有工作流节点必须继承此类并实现 execute 方法
    """

    # 共享事件队列：当不为 None 时，_call_llm 使用 call_with_stream_and_queue
    # 以便 executor 实时读取 thinking 事件
    _event_queue: ClassVar[Optional[queue.Queue]] = None

    @classmethod
    def set_event_queue(cls, q: queue.Queue):
        """设置共享事件队列（executor 在启动 workflow 前调用）"""
        cls._event_queue = q

    @classmethod
    def clear_event_queue(cls):
        """清除事件队列（executor 在 workflow 结束后调用）"""
        cls._event_queue = None
    
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

    def _call_llm(self, question: str, system_prompt: str) -> Tuple[Any, list]:
        """
        公共 LLM 调用（统一 streaming + metrics + thinking）

        当 _event_queue 已设置时，使用 call_with_stream_and_queue 实现
        thinking 事件的实时推送；否则走原有 _call_with_stream_limited 路径。

        Args:
            question: 用户问题
            system_prompt: 节点专用 system prompt

        Returns:
            (response, thinking_events)
        """
        from holmes.core.prompt import build_initial_ask_messages

        tool_executor = getattr(self.holmes_service.ai, "tool_executor", None)

        messages = build_initial_ask_messages(
            initial_user_prompt=question,
            file_paths=None,
            tool_executor=tool_executor,
            runbooks=self.runbook_catalog,
            system_prompt_additions=system_prompt,
        )

        start_time = time.time()
        max_steps = self.holmes_service.get_node_max_steps(self.node_id)

        if self._event_queue is not None:
            # 实时模式：每个 intermediate_event 同时 put 到 queue
            from app.core.holmes.call_wrapper import call_with_stream_and_queue

            original = getattr(self.holmes_service.ai, 'max_steps', None)
            try:
                if original is not None:
                    self.holmes_service.ai.max_steps = max_steps
                response = call_with_stream_and_queue(
                    self.holmes_service.ai,
                    messages,
                    self._event_queue,
                    self.node_id,
                )
            finally:
                if original is not None:
                    self.holmes_service.ai.max_steps = original
        else:
            # 原有路径
            response = self.holmes_service._call_with_stream_limited(messages, max_steps=max_steps)

        llm_duration_ms = (time.time() - start_time) * 1000

        # metrics
        if self.metrics:
            actual_duration = getattr(response, 'duration_ms', llm_duration_ms) or llm_duration_ms
            self.metrics.record_llm_call(self.node_id, actual_duration)
            tc_count = getattr(response, 'tool_call_count', 0) or len(getattr(response, 'tool_calls', []))
            for _ in range(tc_count):
                self.metrics.record_tool_call("llm_tool", 0, success=True)

        thinking_events = getattr(response, 'intermediate_events', []) or []
        return response, thinking_events

    def _save_thinking(self, state: WorkflowState, new_state: dict, thinking_events: list):
        """将 thinking_events 带 node 标记存入 state"""
        prev = state.get("thinking_events", [])
        new_state["thinking_events"] = prev + [
            {**ev, "node": self.node_id} for ev in thinking_events
        ]
