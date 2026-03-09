"""
工作流节点基类

设计原则：
- 高内聚：每个节点封装完整的业务逻辑
- 低耦合：只依赖状态输入，不依赖其他节点
- 可扩展：新增节点只需继承此类
- 数据完整性：通过 _run_with_accumulator 保留所有工具和 AI 中间输出
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, List, Optional

from app.core.workflow.state import WorkflowState
from app.core.workflow.node_accumulator import AccumulatedResult, NodeEventAccumulator

logger = logging.getLogger(__name__)


class WorkflowNode(ABC):
    """
    工作流节点基类
    
    所有工作流节点必须继承此类并实现 execute 方法
    """
    
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

    def _run_with_accumulator(
        self,
        holmes_service: Any,
        system_prompt: str,
        question: str,
        runbook_catalog: Any = None,
    ) -> AccumulatedResult:
        """
        使用 NodeEventAccumulator 运行 HolmesGPT loop，
        捕获所有工具调用结果和 AI 中间消息。

        Args:
            holmes_service: HolmesService 实例
            system_prompt: 节点专用 system prompt
            question: 用户问题
            runbook_catalog: 可选 runbook catalog

        Returns:
            AccumulatedResult，包含完整的工具数据和 AI 消息
        """
        from holmes.core.prompt import build_initial_ask_messages

        tool_executor = getattr(holmes_service.ai, "tool_executor", None)

        messages = build_initial_ask_messages(
            initial_user_prompt=question,
            file_paths=None,
            tool_executor=tool_executor,
            runbooks=runbook_catalog,
            system_prompt_additions=system_prompt,
        )

        sys_prompt = ""
        user_prompt: Optional[str] = None
        extra_msgs: list = []

        for msg in messages:
            role = msg.get("role")
            if role == "system":
                sys_prompt = msg.get("content", "")
            elif role == "user" and user_prompt is None:
                user_prompt = msg.get("content", "")
            else:
                extra_msgs.append(msg)

        accumulator = NodeEventAccumulator()
        result = accumulator.run(
            ai=holmes_service.ai,
            system_prompt=sys_prompt,
            user_prompt=user_prompt,
            msgs=extra_msgs if extra_msgs else None,
        )

        logger.info(
            "📦 [%s] 积累器: %d 工具调用, %d AI 消息, best=%d字符",
            self.node_id,
            len(result.tool_results),
            len(result.ai_messages),
            len(result.best_ai_content),
        )

        return result
