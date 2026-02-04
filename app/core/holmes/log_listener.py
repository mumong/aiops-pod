"""
HolmesGPT 日志监听器

设计目标：
- 不修改 HolmesGPT 框架代码
- 通过 logging.Handler 捕获工具调用日志
- 提取 fetch_runbook 等工具的调用信息
"""

import logging
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ToolCallRecord:
    """工具调用记录"""
    tool_name: str
    call_number: int
    description: str
    output_length: int
    lines: int
    timestamp: float
    runbook_name: Optional[str] = None


class HolmesLogListener(logging.Handler):
    """
    HolmesGPT 日志监听器

    功能：
    - 捕获 holmes.core.tools 和 holmes.core.tool_calling_llm 的日志
    - 解析 fetch_runbook 等工具调用
    - 提取 runbook 名称

    使用方式：
    ```python
    listener = HolmesLogListener()
    logging.getLogger("holmes.core.tools").addHandler(listener)
    logging.getLogger("holmes.core.tool_calling_llm").addHandler(listener)

    # 执行 LLM 调用...

    # 获取捕获的 runbook
    runbooks = listener.get_fetched_runbooks()
    ```
    """

    def __init__(self, level=logging.INFO):
        super().__init__(level)
        self.tool_calls: List[ToolCallRecord] = []
        self.fetched_runbooks: List[str] = []
        self.pattern = re.compile(
            r'Running tool #(\d+) \[bold\](.+?)\[/bold\]: (.+?)\n'
            r'\s*\[dim\]Finished #\d+ in ([\d.]+)s, output length: ([\d,]+) characters \((\d+) lines\)'
        )
        self.runbook_pattern = re.compile(
            r'Runbook:\s*(.+?)(?:\.md|诊断手册|手册|说明)'
        )

    def emit(self, record: logging.LogRecord) -> None:
        """处理日志记录"""
        try:
            message = self.format(record)

            # 尝试匹配工具调用模式
            match = self.pattern.search(message)
            if match:
                call_number = int(match.group(1))
                tool_name = match.group(2)
                description = match.group(3)

                # 提取 runbook 名称
                runbook_match = self.runbook_pattern.search(description)
                runbook_name = runbook_match.group(1) if runbook_match else None

                output_length = int(match.group(4).replace(',', ''))
                lines = int(match.group(5))

                tool_call = ToolCallRecord(
                    tool_name=tool_name,
                    call_number=call_number,
                    description=description,
                    output_length=output_length,
                    lines=lines,
                    timestamp=record.created,
                    runbook_name=runbook_name
                )
                self.tool_calls.append(tool_call)

                # 如果是 fetch_runbook，记录 runbook 名称
                if "fetch_runbook" in tool_name.lower() and runbook_name:
                    if runbook_name not in self.fetched_runbooks:
                        self.fetched_runbooks.append(runbook_name)

        except Exception:
            # 日志处理器不应抛出异常
            pass

    def get_fetched_runbooks(self) -> List[str]:
        """获取所有获取的 runbook 名称"""
        return self.fetched_runbooks.copy()

    def get_tool_calls(self) -> List[ToolCallRecord]:
        """获取所有工具调用记录"""
        return self.tool_calls.copy()

    def get_runbook_summary(self) -> Dict:
        """获取 runbook 使用摘要"""
        return {
            "matched": len(self.fetched_runbooks) > 0,
            "runbook_ids": self.fetched_runbooks.copy(),
            "count": len(self.fetched_runbooks),
            "tool_calls": len([t for t in self.tool_calls if "runbook" in t.tool_name.lower()])
        }

    def get_tool_summary(self) -> Dict:
        """获取工具调用摘要"""
        tool_stats: Dict[str, int] = {}
        for call in self.tool_calls:
            tool_stats[call.tool_name] = tool_stats.get(call.tool_name, 0) + 1

        return {
            "total_calls": len(self.tool_calls),
            "unique_tools": len(tool_stats),
            "tool_counts": tool_stats,
        }

    def clear(self) -> None:
        """清空所有记录"""
        self.tool_calls.clear()
        self.fetched_runbooks.clear()

    def detach(self) -> None:
        """从所有 logger 中移除此 handler"""
        loggers = [
            "holmes.core.tools",
            "holmes.core.tool_calling_llm",
        ]

        for logger_name in loggers:
            logger = logging.getLogger(logger_name)
            if self in logger.handlers:
                logger.removeHandler(self)


def create_log_listener() -> HolmesLogListener:
    """
    创建并配置日志监听器

    Returns:
        HolmesLogListener 实例（需要在调用完成后手动 detach）

    使用示例：
    ```python
    listener = create_log_listener()
    try:
        # 执行操作
        response = ai.call(messages)
    finally:
        listener.detach()
        runbooks = listener.get_fetched_runbooks()
    ```
    """
    listener = HolmesLogListener()
    listener.setFormatter(logging.Formatter('%(message)s'))

    # 添加到 HolmesGPT 相关的 logger
    loggers = [
        "holmes.core.tools",
        "holmes.core.tool_calling_llm",
    ]

    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.addHandler(listener)

    return listener


def create_log_listener_context():
    """
    创建日志监听器上下文管理器

    使用示例：
    ```python
    with create_log_listener_context() as listener:
        response = ai.call(messages)
    runbooks = listener.get_fetched_runbooks()
    ```
    """
    from contextlib import contextmanager

    @contextmanager
    def _listener_context():
        listener = create_log_listener()
        try:
            yield listener
        finally:
            listener.detach()

    return _listener_context()
