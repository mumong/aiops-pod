"""Runbook 目录管理（独立实现，不依赖 HolmesGPT）"""
import json
import os
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RunbookEntry:
    """Runbook 条目"""
    id: str = ""
    description: str = ""
    link: str = ""


class RunbookCatalog:
    """Runbook 目录"""

    def __init__(self, catalog: Optional[List[RunbookEntry]] = None):
        self.catalog: List[RunbookEntry] = catalog or []

    @classmethod
    def from_json(cls, path: str) -> "RunbookCatalog":
        """从 catalog.json 加载"""
        if not os.path.isfile(path):
            logger.warning("⚠️ [Runbook] catalog 文件不存在: %s", path)
            return cls()
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            entries = []
            for item in data:
                entries.append(RunbookEntry(
                    id=item.get("id", ""),
                    description=item.get("description", ""),
                    link=item.get("link", ""),
                ))
            logger.info("📚 [Runbook] 加载 %d 条 Runbook 从 %s", len(entries), path)
            return cls(catalog=entries)
        except Exception as e:
            logger.error("❌ [Runbook] 加载 catalog 失败: %s", e)
            return cls()

    def to_prompt_text(self) -> str:
        """生成注入 system prompt 的 catalog 文本"""
        if not self.catalog:
            return ""
        lines = ["# Available Runbooks",
                 "If one or more runbooks match the issue, use the fetch_runbook tool to get detailed steps for each relevant runbook.", ""]
        for e in self.catalog:
            lines.append(f"- **{e.id}** ({e.link}): {e.description}")
        return "\n".join(lines)

    def __len__(self):
        return len(self.catalog)

    def __bool__(self):
        return bool(self.catalog)
