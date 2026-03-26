#!/usr/bin/env python3
"""
Holmes 配置加载（从 HolmesService.initialize 中抽离）

保持行为不变：
- 读取 YAML
- 进行 ${VAR} / ${VAR:-default} 环境变量替换
- 为了兼容 holmes.Config 的校验：移除顶级非 Holmes 字段后写入临时文件再加载
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml
from holmes.config import Config


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
) -> Config:
    """
    从 YAML 文件加载 Holmes Config
    移除非 Holmes 字段（stream_output, sub_agents, federation, llm）后写入临时文件再加载
    """
    with open(config_file, "r", encoding="utf-8") as f:
        config_dict = yaml.safe_load(f) or {}

    config_dict = substitute_env_vars(config_dict, logger)
    logger.info("✅ 环境变量替换完成")

    _excluded_keys = {"stream_output", "sub_agents", "federation", "llm", "workflow", "metrics"}
    temp_config_dict = {k: v for k, v in config_dict.items() if k not in _excluded_keys}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as temp_file:
        yaml.dump(temp_config_dict, temp_file, allow_unicode=True, default_flow_style=False, sort_keys=False)
        temp_config_path = Path(temp_file.name)

    try:
        kwargs = dict(
            config_file=temp_config_path,
            api_key=api_key,
            model=model,
            max_steps=max_steps,
        )
        if api_base:
            kwargs["api_base"] = api_base
        return Config.load_from_file(**kwargs)
    finally:
        try:
            temp_config_path.unlink()
        except Exception:
            pass
