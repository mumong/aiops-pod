"""应用配置数据类"""
import os
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """应用配置（从 YAML + 环境变量加载）"""
    # LLM
    llm_model: str = "deepseek/deepseek-chat"
    llm_api_key: str = ""
    llm_api_base: str = ""
    # 工作流
    workflow: Dict = field(default_factory=dict)
    # MCP
    mcp_servers: Dict = field(default_factory=dict)
    # 内置工具集
    toolsets: Dict = field(default_factory=dict)
    # 指标
    metrics: Dict = field(default_factory=dict)
    # 联邦
    federation: Dict = field(default_factory=dict)
    # Runbook 路径
    runbook_path: str = "knowledge_base/runbooks"
    # 流式输出
    stream_output: bool = False
    # 原始配置（完整 YAML）
    raw: Dict = field(default_factory=dict)
