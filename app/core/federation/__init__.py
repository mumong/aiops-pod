#!/usr/bin/env python3
"""
联邦查询模块 - 多集群 Agent-to-Agent 联邦查询

公开接口：FederationCoordinator
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import logging
from typing import Any, Dict, Generator, List, Optional

from app.core.federation.registry import AgentRegistry, SubAgentConfig
from app.core.federation.client import SubAgentResult
from app.core.federation.aggregator import FederationAggregator

logger = logging.getLogger(__name__)


class FederationCoordinator:
    """
    联邦查询协调器（懒加载单例）

    使用方式：
        coordinator = FederationCoordinator.from_config(federation_dict, model, api_key)
        async for chunk in coordinator.ask(question, max_steps):
            ...
    """

    def __init__(self, aggregator: FederationAggregator, registry: AgentRegistry):
        self._aggregator = aggregator
        self._registry = registry

    @classmethod
    def from_config(
        cls,
        federation_config: Dict[str, Any],
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> "FederationCoordinator":
        """从 config.yaml 的 federation 配置块创建协调器"""
        registry = AgentRegistry.load_from_dict(federation_config)
        aggregator = FederationAggregator(
            registry=registry,
            max_tokens_per_agent=int(federation_config.get("max_tokens_per_agent", 12000)),
            synthesis_timeout=float(federation_config.get("synthesis_timeout", 300)),
            model=model,
            api_key=api_key,
        )
        return cls(aggregator=aggregator, registry=registry)

    def is_enabled(self) -> bool:
        """检查是否有可用的已启用子集群"""
        return len(self._registry.get_enabled_agents()) > 0

    def ask_stream(self, question: str, max_steps: int = 30, conclusion_max_tokens: int = 8192) -> Generator[str, None, None]:
        """
        执行联邦查询并以流式文本 yield 结果。

        在同步 FastAPI 生成器（或任意同步上下文）中调用。
        内部通过独立线程运行 asyncio，避免与外层事件循环冲突。
        """
        # 在独立线程中运行异步并发查询，确保不受外层 event loop 影响
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                asyncio.run,
                self._aggregator.query_all(question=question, max_steps=max_steps, conclusion_max_tokens=conclusion_max_tokens),
            )
            results = future.result()

        # 汇总各子集群状态
        successful_count = sum(1 for r in results if r.success)
        total_count = len(results)
        logger.info(
            f"[FEDERATION] 并发查询完成：{successful_count}/{total_count} 个子集群成功"
        )

        yield f"🌐 联邦查询：共查询 {total_count} 个子集群，{successful_count} 个成功响应\n\n"

        # 流式合成
        yield from self._aggregator.synthesize(question=question, results=results)


# ============================================================================
# 全局单例
# ============================================================================

_global_coordinator: Optional[FederationCoordinator] = None


def get_federation_coordinator(
    federation_config: Optional[Dict[str, Any]] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Optional[FederationCoordinator]:
    """
    获取全局 FederationCoordinator 单例。

    首次调用需传入 federation_config；后续调用返回已创建的实例。
    若 federation.enabled=false，返回 None。
    """
    global _global_coordinator
    if _global_coordinator is not None:
        return _global_coordinator
    if federation_config is None:
        return None
    if not federation_config.get("enabled", False):
        logger.info("[FEDERATION] federation.enabled=false，跳过联邦初始化")
        return None

    _global_coordinator = FederationCoordinator.from_config(
        federation_config=federation_config,
        model=model,
        api_key=api_key,
    )
    logger.info("[FEDERATION] FederationCoordinator 初始化完成")
    return _global_coordinator
