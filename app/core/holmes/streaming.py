#!/usr/bin/env python3
"""
流式输出相关的小工具（与具体框架无关）
"""

import json
from typing import Optional, Dict


def create_sse_message_cn(event_type: str, data: Optional[Dict] = None) -> str:
    """
    创建 SSE 消息，支持中文输出（不转义为 Unicode）
    """
    if data is None:
        data = {}
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def format_duration(seconds: float) -> str:
    """格式化持续时间为人类可读格式"""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}m {secs:.1f}s"


