#!/usr/bin/env python3
"""
流式文本报告解析器

从 execute_query_stream_text() 的输出中提取"最终答案"部分，
用于给 Master LLM 合成时节省 token，同时保留完整文本用于持久化保存。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ParsedReport:
    """解析后的报告结构"""

    final_answer: str       # 提取的最终答案（给 Master LLM）
    full_text: str          # 完整流式文本（保存到磁盘）
    has_final_answer: bool  # 是否成功提取到最终答案


def extract_final_answer(full_text: str) -> ParsedReport:
    """
    从流式文本输出中提取最终答案部分。

    解析 execute_query_stream_text() 的输出格式：
        --------------------------------------------------
        (空行)
        🎯 最终答案:
        --------------------------------------------------
          内容行（前缀 2 空格缩进）
          ...
        --------------------------------------------------
        (空行)
        📊 总耗时: ...

    Args:
        full_text: execute_query_stream_text() 产生的完整文本

    Returns:
        ParsedReport 包含提取的最终答案和完整文本
    """
    lines = full_text.split("\n")
    answer_lines: list[str] = []
    capturing = False
    # 跳过标记行后的分隔线
    skip_separator = False

    for line in lines:
        stripped = line.strip()

        if not capturing:
            # 查找 "🎯 最终答案:" 标记
            if "🎯 最终答案:" in stripped:
                capturing = True
                skip_separator = True
                continue
        else:
            # 跳过紧跟在标记后面的分隔线
            if skip_separator:
                if stripped.startswith("-" * 10):
                    skip_separator = False
                    continue
                # 如果不是分隔线，直接开始采集
                skip_separator = False

            # 遇到结束分隔线或总耗时行，停止采集
            if stripped.startswith("-" * 10) or "📊 总耗时:" in stripped:
                break

            # 遇到结束的 === 分隔线，停止采集
            if stripped.startswith("=" * 10):
                break

            # 去掉每行前的 2 空格缩进
            if line.startswith("  "):
                answer_lines.append(line[2:])
            else:
                answer_lines.append(line)

    if answer_lines:
        # 去掉首尾空行
        while answer_lines and not answer_lines[0].strip():
            answer_lines.pop(0)
        while answer_lines and not answer_lines[-1].strip():
            answer_lines.pop()

    final_answer = "\n".join(answer_lines)

    return ParsedReport(
        final_answer=final_answer if final_answer else full_text,
        full_text=full_text,
        has_final_answer=bool(final_answer),
    )
