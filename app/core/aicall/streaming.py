"""流式事件处理：将 LLM 调用过程中的事件推送到 queue"""
import queue
import time
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def push_event(
    event_queue: Optional[queue.Queue],
    event_type: str,
    node_id: str = "",
    **data,
) -> None:
    """推送 thinking 事件到 queue（非阻塞）

    Args:
        event_queue: 目标队列，None 则静默跳过
        event_type: 事件类型 (tool_start / tool_result / ai_message / iteration_end)
        node_id: 所属节点 ID
        **data: 事件附加数据
    """
    if not event_queue:
        return
    event: Dict = {
        "type": event_type,
        "node": node_id,
        "timestamp": time.time(),
        **data,
    }
    try:
        event_queue.put_nowait(("thinking", event))
    except queue.Full:
        logger.debug("Event queue full, dropping: %s", event_type)
