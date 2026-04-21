#!/usr/bin/env python3
"""
Holmes 配置加载（从 HolmesService.initialize 中抽离）

保持行为不变：
- 读取 YAML
- 进行 ${VAR} / ${VAR:-default} 环境变量替换
- 返回本项目的轻量配置对象，避免引入 Holmes 全量 toolset 依赖
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

from app.core.config import AppConfig, ConfigLoader


def load_stream_output_flag(config_file: Path, logger) -> bool:
    """
    从配置文件读取 stream_output（顶级字段）
    """
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f) or {}
        stream_output = bool(config_dict.get("stream_output", False))
        output_mode = "流式输出 (stream)" if stream_output else "非流式输出 (invoke)"
        logger.info(f"📡 输出模式: {output_mode}")
        return stream_output
    except Exception as e:
        logger.warning(f"读取流式输出配置失败，使用默认值（非流式）: {e}")
        return False


def substitute_env_vars(obj: Any, logger, depth: int = 0) -> Any:
    """
    递归替换配置中的环境变量占位符

    支持语法:
      - ${VAR}           使用环境变量 VAR 的值，不存在则保留原字符串
      - ${VAR:-default}  使用环境变量 VAR 的值，不存在则使用 default
    """
    if depth > 50:
        return obj

    if isinstance(obj, dict):
        return {k: substitute_env_vars(v, logger, depth + 1) for k, v in obj.items()}
    if isinstance(obj, list):
        return [substitute_env_vars(item, logger, depth + 1) for item in obj]
    if not isinstance(obj, str):
        return obj

    pattern = r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}"

    def replace_match(match: re.Match) -> str:
        var_name = match.group(1)
        default_value = match.group(2)

        env_value = os.environ.get(var_name)
        if env_value is not None:
            logger.debug(f"🔄 环境变量替换: ${{{var_name}}} -> ***")
            return env_value
        if default_value is not None:
            logger.debug(f"🔄 使用默认值: ${{{var_name}}} -> {default_value}")
            return default_value

        logger.warning(f"⚠️ 环境变量未设置: {var_name}")
        return match.group(0)

    return re.sub(pattern, replace_match, obj)


def load_holmes_config_from_yaml(
    *,
    config_file: Path,
    api_key: str,
    model: str,
    max_steps: int,
    api_base: str = None,
    logger,
) -> AppConfig:
    """
    从 YAML 文件加载轻量配置对象
    """
    logger.info("✅ 环境变量替换完成")
    return ConfigLoader.load(
        config_file,
        api_key=api_key,
        model=model,
        max_steps=max_steps,
        api_base=api_base,
    )
