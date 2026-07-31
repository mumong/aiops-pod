"""Import-only fixture proving offline replay dependencies stay local."""

import asyncio
import os
import socket
import subprocess
import sys
from pathlib import Path


os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"


class OfflineReplayGuard:
    guarded_categories = [
        "network",
        "subprocess",
        "llm",
        "mcp",
        "kubernetes",
    ]

    def __init__(self):
        self.attempts = []
        self.guarded_entrypoints = {
            category: [] for category in self.guarded_categories
        }
        self.enforced = False

    def _blocked(self, category, entrypoint, args, kwargs):
        attempt = {
            "category": category,
            "entrypoint": entrypoint,
            "args": [repr(value) for value in args[:3]],
            "kwargs": {
                str(key): repr(value)
                for key, value in list(kwargs.items())[:6]
            },
        }
        self.attempts.append(attempt)
        raise RuntimeError(
            f"offline replay blocked {category} access via {entrypoint}"
        )

    def _patch(self, owner, attribute, category, entrypoint):
        if not hasattr(owner, attribute):
            return

        def blocker(*args, **kwargs):
            return self._blocked(
                category,
                entrypoint,
                args,
                kwargs,
            )

        setattr(owner, attribute, blocker)
        self.guarded_entrypoints[category].append(entrypoint)

    def install_system_guards(self):
        self._patch(
            socket.socket,
            "connect",
            "network",
            "socket.socket.connect",
        )
        self._patch(
            socket.socket,
            "connect_ex",
            "network",
            "socket.socket.connect_ex",
        )
        self._patch(
            socket.socket,
            "sendto",
            "network",
            "socket.socket.sendto",
        )
        self._patch(
            socket,
            "create_connection",
            "network",
            "socket.create_connection",
        )
        for attribute in (
            "Popen",
            "run",
            "call",
            "check_call",
            "check_output",
        ):
            self._patch(
                subprocess,
                attribute,
                "subprocess",
                f"subprocess.{attribute}",
            )
        self._patch(os, "system", "subprocess", "os.system")
        self._patch(
            asyncio,
            "create_subprocess_exec",
            "subprocess",
            "asyncio.create_subprocess_exec",
        )
        self._patch(
            asyncio,
            "create_subprocess_shell",
            "subprocess",
            "asyncio.create_subprocess_shell",
        )

    def install_client_guards(self):
        from app.core.aicall import client as aicall_client
        from app.core.aicall import tools as aicall_tools
        from app.core.mcp import manager as mcp_manager

        for attribute in (
            "_create_chat_model",
            "call",
            "call_simple",
            "call_simple_json",
            "call_structured",
        ):
            self._patch(
                aicall_client.AICall,
                attribute,
                "llm",
                f"AICall.{attribute}",
            )
        for attribute in (
            "invoke",
            "ainvoke",
            "stream",
            "astream",
        ):
            self._patch(
                aicall_client.ChatOpenAI,
                attribute,
                "llm",
                f"ChatOpenAI.{attribute}",
            )

        self._patch(
            aicall_tools,
            "load_mcp_tools",
            "mcp",
            "app.core.aicall.tools.load_mcp_tools",
        )
        for attribute in (
            "start_server",
            "start_all",
            "_check_health",
        ):
            self._patch(
                mcp_manager.MCPServerManager,
                attribute,
                "mcp",
                f"MCPServerManager.{attribute}",
            )
        for attribute in (
            "get_mcp_manager",
            "auto_start_mcp_servers",
        ):
            self._patch(
                mcp_manager,
                attribute,
                "mcp",
                f"app.core.mcp.manager.{attribute}",
            )

        from kubernetes import client as kubernetes_client
        from kubernetes import config as kubernetes_config
        from kubernetes import dynamic as kubernetes_dynamic

        self._patch(
            kubernetes_client.ApiClient,
            "call_api",
            "kubernetes",
            "kubernetes.client.ApiClient.call_api",
        )
        for attribute in (
            "load_kube_config",
            "load_incluster_config",
        ):
            self._patch(
                kubernetes_config,
                attribute,
                "kubernetes",
                f"kubernetes.config.{attribute}",
            )
        self._patch(
            kubernetes_dynamic.DynamicClient,
            "request",
            "kubernetes",
            "kubernetes.dynamic.DynamicClient.request",
        )
        self.enforced = all(
            self.guarded_entrypoints[category]
            for category in self.guarded_categories
        )

    def audit(self):
        return {
            "enforced": self.enforced,
            "attempt_count": len(self.attempts),
            "attempts": list(self.attempts),
            "guarded_categories": list(self.guarded_categories),
            "guarded_entrypoints": {
                category: list(entrypoints)
                for category, entrypoints
                in self.guarded_entrypoints.items()
            },
        }


OFFLINE_GUARD = OfflineReplayGuard()
OFFLINE_GUARD.install_system_guards()

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.core.workflow import fact_contract as _fact_contract  # noqa: E402,F401
from app.core.workflow.nodes import conclusion_formatter as _conclusion  # noqa: E402,F401


OFFLINE_GUARD.install_client_guards()
