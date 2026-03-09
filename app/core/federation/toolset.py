#!/usr/bin/env python3
"""
联邦查询工具集 - 用于主 Agent 的 Tool Calling

包含工具：
- list_clusters: 列出所有可用的子集群
- query_cluster: 查询特定子集群
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from holmes.core.tools import Tool, Toolset, ToolsetStatusEnum
from pydantic import Field, PrivateAttr

from app.core.federation.registry import AgentRegistry
from app.core.federation.client import SubAgentClient

logger = logging.getLogger(__name__)


class ListClustersTool(Tool):
    """列出所有可用的子集群"""

    name: str = "list_clusters"
    description: str = "列出所有可用的子集群信息，包括名称、URL 和描述"

    def _invoke(self, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行工具调用"""
        registry: AgentRegistry = context.get("federation_registry") if context else None
        if not registry:
            return {"error": "Federation registry not available"}

        clusters = registry.get_enabled_agents()
        return {
            "total": len(clusters),
            "clusters": [
                {
                    "name": c.name,
                    "url": c.url,
                    "description": c.description or "无描述"
                }
                for c in clusters
            ]
        }

    def get_parameterized_one_liner(self, params: Dict[str, Any]) -> str:
        return "list_clusters()"


class QueryClusterTool(Tool):
    """查询特定子集群"""

    name: str = "query_cluster"
    description: str = (
        "查询特定子集群的诊断信息。"
        "参数：cluster_name（集群名称），question（要查询的问题），"
        "max_steps（最大执行步数，默认30），conclusion_max_tokens（结论最大token数，默认8192）"
    )

    def _invoke(self, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行工具调用"""
        cluster_name = params.get("cluster_name")
        question = params.get("question")
        max_steps = params.get("max_steps", 30)
        conclusion_max_tokens = params.get("conclusion_max_tokens", 8192)

        if not cluster_name or not question:
            return {"error": "Missing required parameters: cluster_name and question"}

        registry: AgentRegistry = context.get("federation_registry") if context else None
        if not registry:
            return {"error": "Federation registry not available"}

        # 查找集群配置
        agent = None
        for a in registry.get_enabled_agents():
            if a.name == cluster_name:
                agent = a
                break

        if not agent:
            return {
                "error": f"Cluster '{cluster_name}' not found",
                "available_clusters": [a.name for a in registry.get_enabled_agents()]
            }

        # 调用子集群（同步包装异步调用）
        client = SubAgentClient()

        def sync_query():
            return asyncio.run(
                client.query(
                    agent=agent,
                    question=question,
                    max_steps=max_steps,
                    conclusion_max_tokens=conclusion_max_tokens,
                    timeout=300.0
                )
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(sync_query)
            result = future.result()

        if result.success:
            self._save_report(cluster_name, result)
            return {
                "cluster": cluster_name,
                "success": True,
                "response": result.text,
                "elapsed_seconds": result.elapsed_seconds
            }
        else:
            return {
                "cluster": cluster_name,
                "success": False,
                "error": result.error,
                "elapsed_seconds": result.elapsed_seconds
            }

    def get_parameterized_one_liner(self, params: Dict[str, Any]) -> str:
        cluster = params.get("cluster_name", "?")
        question = params.get("question", "?")
        return f"query_cluster(cluster_name='{cluster}', question='{question[:30]}...')"

    def _save_report(self, cluster_name: str, result: Dict[str, Any]) -> None:
        """保存子集群报告到本地 reports/ 目录"""
        try:
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{cluster_name}_{timestamp}.md"
            filepath = reports_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# 子集群诊断报告 - {cluster_name}\n\n")
                f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**来源**: Agent-to-Agent (v2)\n")
                f.write(f"**耗时**: {result.elapsed_seconds:.1f} 秒\n\n")
                f.write("---\n\n")
                f.write(result.text)

            logger.info(f"[FEDERATION A2A] 已保存 {cluster_name} 报告到: {filepath}")
        except Exception as exc:
            logger.error(f"[FEDERATION A2A] 保存报告失败: {exc}", exc_info=True)


class FederationToolset(Toolset):
    """联邦查询工具集"""

    _registry: AgentRegistry = PrivateAttr()
    _tools: list = PrivateAttr()

    def __init__(self, registry: AgentRegistry):
        super().__init__(
            name="federation",
            description="联邦查询工具集，用于多集群智能路由和查询",
            tools=[]
        )
        self._registry = registry
        self._tools = [
            ListClustersTool(),
            QueryClusterTool()
        ]

    @classmethod
    def get_example_config(cls) -> Dict[str, Any]:
        return {
            "enabled": True,
            "description": "联邦查询工具集，用于多集群智能路由和查询"
        }

    def get_tools(self) -> list[Tool]:
        return self._tools

    def get_tool_by_name(self, name: str) -> Optional[Tool]:
        for tool in self._tools:
            if tool.name == name:
                return tool
        return None

    def get_context(self) -> Dict[str, Any]:
        """提供工具执行所需的上下文"""
        return {
            "federation_registry": self._registry
        }
