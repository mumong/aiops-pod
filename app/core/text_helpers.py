#!/usr/bin/env python3
"""
文本处理辅助函数

提取重复的文本处理逻辑，提高代码复用性
"""

from typing import Dict, List, Any, Callable, Optional
from app.core.constants import MAX_QUESTION_DISPLAY_LENGTH


def truncate_question(question: str, max_length: int = MAX_QUESTION_DISPLAY_LENGTH) -> str:
    """
    截断问题文本用于显示

    如果问题超过 max_length，返回截断后的字符串加上省略号
    否则返回原字符串

    Args:
        question: 原始问题文本
        max_length: 最大显示长度（默认使用 MAX_QUESTION_DISPLAY_LENGTH）

    Returns:
        截断后的问题文本
    """
    if len(question) > max_length:
        return f"{question[:max_length]}..."
    return question


def truncate_error(error: str, max_length: int = 120) -> str:
    """
    截断错误消息用于显示

    Args:
        error: 原始错误消息
        max_length: 最大显示长度（默认 120）

    Returns:
        截断后的错误消息
    """
    if len(error) > max_length:
        return f"{error[:max_length]}..."
    return error


def truncate_preview(text: str, max_length: int = 500) -> str:
    """
    截断预览文本（用于日志和 UI 显示）

    Args:
        text: 原始文本
        max_length: 最大预览长度（默认 500）

    Returns:
        截断后的文本
    """
    if len(text) > max_length:
        return f"{text[:max_length]}..."
    return text


def emit_text(text: str) -> str:
    """
    发出带换行的文本（用于流式输出）

    Args:
        text: 原始文本

    Returns:
        带换行的文本
    """
    return f"{text}\n"


# ============================================================================
# 节点输出框图格式化
# ============================================================================

def draw_box_start(title: str) -> str:
    """
    绘制 ASCII 边框开始部分

    Args:
        title: 框标题

    Returns:
        格式化后的边框开始字符串
    """
    width = 50
    line = "─" * width
    padding = (width - len(title) - 4) // 2
    title_with_padding = " " * padding + title + " " * padding
    return f"┌{line}┐\n│{title_with_padding}│\n"


def draw_box_end() -> str:
    """
    绘制 ASCII 边框结束部分

    Returns:
        格式化后的边框结束字符串
    """
    width = 50
    line = "─" * width
    return f"└{line}┘\n"


def format_node_box(node_id: str, title: str, content_lines: list) -> str:
    """
    格式化节点输出的框图

    Args:
        node_id: 节点ID（用于识别）
        title: 框标题
        content_lines: 内容行列表

    Returns:
        格式化后的完整输出字符串
    """
    width = 50
    lines = []
    lines.append(draw_box_start(title))

    # 每行内容用 │ 包裹，并补齐宽度
    for line in content_lines:
        # 计算需要填充的空格：总宽度50 - 左边框1 - 右边框1
        max_content_width = width - 2
        if len(line) > max_content_width:
            # 内容过长，截断
            line = line[:max_content_width - 3] + "..."
        padding = max_content_width - len(line)
        lines.append(f"│{line}{' ' * padding}│")

    lines.append(draw_box_end())
    return "".join(lines)


NODE_TITLES = {
    "layer": "📊 问题定位结果",
    "evidence": "🔍 证据采集结果",
    "rca": "🎯 根因分析结果",
    "conclusion": "📋 汇总总结结果",
}


# ============================================================================
# 节点配置注册系统（支持动态扩展）
# ============================================================================

class NodeConfig:
    """节点配置（支持动态注册）"""

    def __init__(
        self,
        node_id: str,
        title: str,
        content_formatter: Optional[Callable[[Dict[str, Any]], List[str]]] = None
    ):
        """
        初始化节点配置

        Args:
            node_id: 节点ID
            title: 节点标题
            content_formatter: 从snapshot提取内容行的函数（可选）
        """
        self.node_id = node_id
        self.title = title
        self.content_formatter = content_formatter or (lambda s: [])

    def get_title(self) -> str:
        """获取节点标题"""
        return self.title

    def format_content(self, snapshot: Dict[str, Any]) -> List[str]:
        """格式化节点内容"""
        return self.content_formatter(snapshot)


# 默认节点配置（当前4节点）
def _default_layer_formatter(snapshot: Dict[str, Any]) -> List[str]:
    """Layer节点默认格式化"""
    return [
        f"   层级: {snapshot.get('layer', '?')}",
        f"   置信度: {snapshot.get('layer_confidence', 0) or 0:.0%}",
    ]


def _default_evidence_formatter(snapshot: Dict[str, Any]) -> List[str]:
    """Evidence节点默认格式化"""
    count = snapshot.get("evidence_count", 0)
    collected = snapshot.get("collected_count", 0)
    completeness = snapshot.get("completeness", 0) or 0
    return [
        f"   证据: {collected}/{count} 项, 完整度: {completeness:.0%}",
    ]


def _default_rca_formatter(snapshot: Dict[str, Any]) -> List[str]:
    """RCA节点默认格式化"""
    content_lines = []
    root_cause = snapshot.get("root_cause", "")
    conf = snapshot.get("confidence")
    conf_str = f"{conf:.0%}" if conf else "?"

    if root_cause:
        content_lines.append(f"   根因: {root_cause}")
    content_lines.append(f"   置信度: {conf_str}")

    # 因果链
    causal_chain = snapshot.get("causal_chain", {})
    if causal_chain:
        content_lines.append("")
        content_lines.append("   🔗 因果链:")
        trigger = causal_chain.get("trigger") or causal_chain.get("root_cause", "")
        mechanism = causal_chain.get("mechanism") or causal_chain.get("propagation", "")
        manifestation = causal_chain.get("manifestation", "")
        if trigger:
            content_lines.append(f"     根本原因: {trigger}")
        if mechanism:
            content_lines.append(f"     传导机制: {mechanism}")
        if manifestation:
            content_lines.append(f"     最终表现: {manifestation}")

    return content_lines


def _default_conclusion_formatter(snapshot: Dict[str, Any]) -> List[str]:
    """Conclusion节点默认格式化"""
    length = snapshot.get("conclusion_length", 0)
    return [
        f"   报告长度: {length} 字符",
    ]


# 默认节点注册表
DEFAULT_NODE_CONFIGS: Dict[str, NodeConfig] = {
    "layer": NodeConfig("layer", NODE_TITLES["layer"], _default_layer_formatter),
    "evidence": NodeConfig("evidence", NODE_TITLES["evidence"], _default_evidence_formatter),
    "rca": NodeConfig("rca", NODE_TITLES["rca"], _default_rca_formatter),
    "conclusion": NodeConfig("conclusion", NODE_TITLES["conclusion"], _default_conclusion_formatter),
}


def get_node_config(node_id: str, custom_configs: Optional[Dict[str, NodeConfig]] = None) -> Optional[NodeConfig]:
    """
    获取节点配置（支持动态扩展）

    Args:
        node_id: 节点ID
        custom_configs: 自定义节点配置字典（可选）

    Returns:
        节点配置，如果未找到返回 None
    """
    configs = custom_configs or DEFAULT_NODE_CONFIGS
    return configs.get(node_id)


def get_all_registered_node_ids(custom_configs: Optional[Dict[str, NodeConfig]] = None) -> List[str]:
    """
    获取所有已注册的节点ID列表

    Args:
        custom_configs: 自定义节点配置字典（可选）

    Returns:
        节点ID列表
    """
    configs = custom_configs or DEFAULT_NODE_CONFIGS
    return list(configs.keys())
