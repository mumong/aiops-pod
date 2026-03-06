#!/usr/bin/env python3
"""
联邦查询 - 子集群注册表

从配置文件的 federation.sub_agents 列表加载子集群配置，支持运行时感知。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict

logger = logging.getLogger(__name__)


@dataclass
class SubAgentConfig:
    """子集群配置"""
    name: str
    url: str
    description: str = ""
    enabled: bool = True

    def __post_init__(self):
        # 规范化 URL：去掉末尾斜杠
        self.url = self.url.rstrip("/")


class AgentRegistry:
    """子集群注册表，从配置字典加载"""

    def __init__(self, agents: List[SubAgentConfig]):
        self._agents = agents

    @classmethod
    def load_from_dict(cls, federation_config: Dict[str, Any]) -> "AgentRegistry":
        """
        从 config.yaml 的 federation 配置块加载注册表。

        federation_config 示例:
          {
            "enabled": true,
            "sub_agents": [
              {"name": "cluster-24", "url": "http://10.2.0.24:30800", "enabled": true}
            ]
          }
        """
        raw_agents = federation_config.get("sub_agents", [])
        agents: List[SubAgentConfig] = []

        for item in raw_agents:
            if not isinstance(item, dict):
                logger.warning(f"[FEDERATION] 跳过非法 sub_agent 配置项: {item}")
                continue
            name = item.get("name", "")
            url = item.get("url", "")
            if not name or not url:
                logger.warning(f"[FEDERATION] sub_agent 缺少 name 或 url，跳过: {item}")
                continue
            agents.append(SubAgentConfig(
                name=name,
                url=url,
                description=item.get("description", ""),
                enabled=bool(item.get("enabled", True)),
            ))

        logger.info(f"[FEDERATION] 注册表加载完成，共 {len(agents)} 个子集群")
        return cls(agents)

    def get_enabled_agents(self) -> List[SubAgentConfig]:
        """返回所有已启用的子集群"""
        enabled = [a for a in self._agents if a.enabled]
        logger.debug(f"[FEDERATION] 已启用子集群: {[a.name for a in enabled]}")
        return enabled

    def __len__(self) -> int:
        return len(self._agents)
