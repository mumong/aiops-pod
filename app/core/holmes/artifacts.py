#!/usr/bin/env python3
"""
超大输出的轻量 artifact 存储（内存版）

目的：避免 tool result/日志等过长时只能截断导致“信息丢失”。
注意：这是可扩展点；未来可替换为持久化存储（S3/MinIO/Redis 等）。
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class Artifact:
    id: str
    content: str
    created_at_ms: int
    content_type: str = "text/plain; charset=utf-8"


class ArtifactStore:
    def __init__(self, *, max_items: int = 200, ttl_seconds: int = 60 * 30):
        self._items: Dict[str, Artifact] = {}
        self._max_items = max_items
        self._ttl_seconds = ttl_seconds

    def put(self, content: str, *, content_type: str = "text/plain; charset=utf-8") -> str:
        self._gc()
        if len(self._items) >= self._max_items:
            # 简单策略：清掉最老的一个
            oldest_id = min(self._items.values(), key=lambda a: a.created_at_ms).id
            self._items.pop(oldest_id, None)

        artifact_id = uuid.uuid4().hex[:16]
        self._items[artifact_id] = Artifact(
            id=artifact_id,
            content=content,
            created_at_ms=int(time.time() * 1000),
            content_type=content_type,
        )
        return artifact_id

    def get(self, artifact_id: str) -> Optional[Artifact]:
        self._gc()
        return self._items.get(artifact_id)

    def _gc(self) -> None:
        if not self._items:
            return
        cutoff_ms = int((time.time() - self._ttl_seconds) * 1000)
        to_delete = [k for k, v in self._items.items() if v.created_at_ms < cutoff_ms]
        for k in to_delete:
            self._items.pop(k, None)


_global_store: Optional[ArtifactStore] = None


def get_artifact_store() -> ArtifactStore:
    global _global_store
    if _global_store is None:
        _global_store = ArtifactStore()
    return _global_store


