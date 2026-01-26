"""
工作流节点基类

设计原则：
- 高内聚：每个节点封装完整的业务逻辑
- 低耦合：只依赖状态输入，不依赖其他节点
- 可扩展：新增节点只需继承此类
"""

from abc import ABC, abstractmethod
from typing import List
from app.core.workflow.state import WorkflowState


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
