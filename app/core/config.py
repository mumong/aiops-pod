#!/usr/bin/env python3
"""
Lightweight app config loader.

Only keep the fields this project actually uses at runtime so startup does not
pull in Holmes' full toolset dependency graph.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from holmes.plugins.runbooks import RunbookCatalog, load_runbook_catalog

logger = logging.getLogger(__name__)

_ENV_VAR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


@dataclass
class AppConfig:
    llm_model: str = "deepseek/deepseek-chat"
    llm_api_key: str = ""
    llm_api_base: Optional[str] = None
    max_steps: int = 50
    mcp_servers: Dict[str, Any] = field(default_factory=dict)
    custom_runbook_catalogs: List[Union[str, Path]] = field(default_factory=list)
    raw_config: Dict[str, Any] = field(default_factory=dict)

    @property
    def model(self) -> str:
        return self.llm_model

    @property
    def api_key(self) -> str:
        return self.llm_api_key

    @property
    def api_base(self) -> Optional[str]:
        return self.llm_api_base

    def get_runbook_catalog(self) -> Optional[RunbookCatalog]:
        try:
            return load_runbook_catalog(
                dal=None,
                custom_catalog_paths=self.custom_runbook_catalogs or None,
            )
        except Exception as exc:
            logger.warning("加载内置 runbook catalog 失败: %s", exc)
            return None


class ConfigLoader:
    @staticmethod
    def _substitute_env_vars(obj: Any, depth: int = 0) -> Any:
        if depth > 50:
            return obj

        if isinstance(obj, dict):
            return {
                key: ConfigLoader._substitute_env_vars(value, depth + 1)
                for key, value in obj.items()
            }
        if isinstance(obj, list):
            return [ConfigLoader._substitute_env_vars(item, depth + 1) for item in obj]
        if not isinstance(obj, str):
            return obj

        def replace_match(match: re.Match) -> str:
            var_name = match.group(1)
            default_value = match.group(2)
            env_value = os.environ.get(var_name)
            if env_value is not None:
                return env_value
            if default_value is not None:
                return default_value
            return match.group(0)

        return _ENV_VAR_PATTERN.sub(replace_match, obj)

    @classmethod
    def load(
        cls,
        config_file: str | Path,
        *,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_steps: int = 50,
        api_base: Optional[str] = None,
    ) -> AppConfig:
        path = Path(config_file)
        raw_config: Dict[str, Any] = {}
        if path.exists():
            with open(path, "r", encoding="utf-8") as file:
                raw_config = yaml.safe_load(file) or {}
            raw_config = cls._substitute_env_vars(raw_config)

        llm_config = raw_config.get("llm", {}) or {}
        final_model = model or llm_config.get("model") or "deepseek/deepseek-chat"
        final_api_key = api_key or llm_config.get("api_key") or ""
        final_api_base = api_base
        if final_api_base is None:
            final_api_base = llm_config.get("api_base")

        return AppConfig(
            llm_model=final_model,
            llm_api_key=final_api_key,
            llm_api_base=final_api_base,
            max_steps=max_steps,
            mcp_servers=raw_config.get("mcp_servers", {}) or {},
            custom_runbook_catalogs=raw_config.get("custom_runbook_catalogs", []) or [],
            raw_config=raw_config,
        )
