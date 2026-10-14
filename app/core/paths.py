#!/usr/bin/env python3
"""
路径与项目结构辅助

目标：
- 统一获取项目根目录的方式（减少重复实现、降低耦合）
"""

from pathlib import Path


def get_project_root() -> Path:
    """获取项目根目录（repo root）"""
    # app/core/paths.py -> app/core -> app -> repo root
    return Path(__file__).parent.parent.parent




def get_app_version() -> str:
    """Single version source: the VERSION file shipped next to app/ (also in the image)."""
    try:
        return (get_project_root() / "VERSION").read_text(encoding="utf-8").strip() or "unknown"
    except OSError:
        return "unknown"
