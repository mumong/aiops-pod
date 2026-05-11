# app/core/aicall/types.py
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AICallResult:
    """AI 调用结果（兼容现有 StreamResponse 接口）"""
    result: str = ""
    tool_calls: List[Dict] = field(default_factory=list)
    iterations: int = 0
    tool_call_count: int = 0
    duration_ms: float = 0.0
    intermediate_events: List[Dict] = field(default_factory=list)
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    structured_response: Optional[Any] = None


@dataclass
class ThinkingEvent:
    """思考事件（实时推送到 stream_queue）"""
    type: str          # ai_message, tool_start, tool_result, iteration_end
    node: str = ""     # 所属节点 ID
    data: Dict = field(default_factory=dict)
    timestamp: float = 0.0
