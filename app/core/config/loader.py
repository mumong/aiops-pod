"""配置加载器 — 从 YAML + 环境变量加载 AppConfig"""
import os
import re
import logging
from pathlib import Path
from typing import Optional

import yaml

from .settings import AppConfig

logger = logging.getLogger(__name__)


class ConfigLoader:
    """配置加载器"""

    @staticmethod
    def load(config_path: str | Path) -> AppConfig:
        """加载配置文件并应用环境变量覆盖"""
        config_path = Path(config_path)

        if not config_path.exists():
            logger.warning("⚠️ [Config] 配置文件不存在: %s，使用默认配置", config_path)
            return ConfigLoader._apply_env_overrides(AppConfig())

        logger.info("🔧 [Config] 加载配置: %s", config_path)
        with open(config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

        # 环境变量替换 ${VAR:-default}
        raw = ConfigLoader._substitute_env_vars(raw)

        llm_cfg = raw.get("llm", {}) or {}

        config = AppConfig(
            llm_model=llm_cfg.get("model", "deepseek/deepseek-chat"),
            llm_api_key=llm_cfg.get("api_key", ""),
            llm_api_base=llm_cfg.get("api_base", ""),
            workflow=raw.get("workflow", {}),
            mcp_servers=raw.get("mcp_servers", {}),
            toolsets=raw.get("toolsets", {}),
            metrics=raw.get("metrics", {}),
            federation=raw.get("federation", {}),
            stream_output=raw.get("stream_output", False),
            raw=raw,
        )

        # 环境变量覆盖
        config = ConfigLoader._apply_env_overrides(config)

        logger.info("✅ [Config] 配置加载完成 | model=%s", config.llm_model)
        return config

    @staticmethod
    def _apply_env_overrides(config: AppConfig) -> AppConfig:
        """环境变量覆盖（优先级最高）"""
        env_key = os.getenv("LLM_API_KEY")
        env_model = os.getenv("LLM_MODEL")
        env_base = os.getenv("LLM_API_BASE")

        if env_key:
            config.llm_api_key = env_key
        if env_model and env_model.strip():
            config.llm_model = env_model
        if env_base and env_base.strip():
            config.llm_api_base = env_base

        return config

    @staticmethod
    def _substitute_env_vars(data, _depth=0):
        """递归替换 ${VAR:-default} 语法"""
        if _depth > 20:
            return data
        if isinstance(data, str):
            def _replace(m):
                var_name = m.group(1)
                default = m.group(3) if m.group(3) is not None else ""
                return os.getenv(var_name, default)
            return re.sub(r'\$\{(\w+)(:-([^}]*))?\}', _replace, data)
        elif isinstance(data, dict):
            return {k: ConfigLoader._substitute_env_vars(v, _depth + 1) for k, v in data.items()}
        elif isinstance(data, list):
            return [ConfigLoader._substitute_env_vars(item, _depth + 1) for item in data]
        return data
