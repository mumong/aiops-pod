#!/usr/bin/env python3
"""
AIOps Copilot Service
负责 AI 服务的初始化、配置和查询执行
唯一模式：AICall (LangGraph) + Workflow
"""
import os
import logging
import threading
import json
from pathlib import Path
from typing import Optional, Tuple, Any, Generator, Dict
from datetime import datetime

from holmes.plugins.runbooks import RunbookCatalog

from app.core.config import AppConfig
from app.core.runbook import RunbookManager
from app.core.paths import get_project_root
from app.core.environment import get_config_file_path
from app.core.holmes.streaming import create_sse_message_cn, format_duration
from app.core.holmes.config_loader import load_holmes_config_from_yaml
from app.core.holmes.tool_logging_patch import apply_tool_result_logging_patch
from app.core.federation import get_federation_coordinator, FederationCoordinator, get_federation_agent, FederationAgent
from app.core.aicall import AICall

logger = logging.getLogger(__name__)

# 使每次工具调用的输出与错误写入 app 日志，便于调试 MCP
apply_tool_result_logging_patch()


def _short_cell(value: Any, max_chars: int = 80) -> str:
    text = str(value or "").replace("\n", " ").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def format_evidence_plan_output(evidence_analysis: Any, max_items: int = 12) -> str:
    """Render evidence_plan for visible workflow output.

    The raw JSON is still archived. This function provides a compact table for
    curl/frontend users so they can see what the evidence node planned and
    which planned items were satisfied.
    """
    if not evidence_analysis:
        return ""
    if isinstance(evidence_analysis, str):
        try:
            data = json.loads(evidence_analysis)
        except Exception:
            return ""
    elif isinstance(evidence_analysis, dict):
        data = evidence_analysis
    else:
        return ""

    plan = data.get("evidence_plan") or []
    if not isinstance(plan, list) or not plan:
        return ""

    inventory = data.get("evidence_inventory") or []
    collected_by_id = {
        str(item.get("id")): bool(item.get("collected"))
        for item in inventory
        if isinstance(item, dict) and item.get("id") is not None
    }

    lines = [
        "   📋 证据采集计划",
        "   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |",
        "   |----|------|------|------|----------|------|",
    ]
    for item in plan[:max_items]:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("id") or "?")
        if item_id in collected_by_id:
            status = "✅" if collected_by_id[item_id] else "❌"
        else:
            status = "待确认"
        lines.append(
            "   "
            f"| {_short_cell(item_id, 16)} "
            f"| {_short_cell(item.get('level'), 12)} "
            f"| {status} "
            f"| {_short_cell(item.get('tool'), 28)} "
            f"| {_short_cell(item.get('description') or item.get('purpose'), 48)} "
            f"| `{_short_cell(item.get('command'), 80)}` |"
        )

    if len(plan) > max_items:
        lines.append(f"   ... 还有 {len(plan) - max_items} 项计划未展开")

    missing_reasons = data.get("missing_reasons") or []
    if missing_reasons:
        lines.append("")
        lines.append("   ⚠️ 未采集原因:")
        for reason in missing_reasons[:5]:
            lines.append(f"   - {_short_cell(reason, 140)}")
        if len(missing_reasons) > 5:
            lines.append(f"   - ... 还有 {len(missing_reasons) - 5} 条")

    return "\n".join(lines)


def configure_model_context_window(llm_config: Optional[Dict[str, Any]] = None) -> Optional[int]:
    """Expose model context window as MODEL_CONTEXT_WINDOW for budget estimation.

    Runtime env remains the strongest source. Config supports either
    llm.context_window or llm.model_context_window so deployment manifests can
    keep model identity and context capacity in one place.
    """
    env_value = os.getenv("MODEL_CONTEXT_WINDOW", "").strip()
    if env_value.isdigit():
        return int(env_value)

    cfg = llm_config or {}
    for key in ("context_window", "model_context_window", "max_context_window"):
        value = cfg.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        if not text.isdigit():
            logger.warning("⚠️ [context_budget] 忽略无效 llm.%s=%r，必须是正整数 token 数", key, value)
            return None
        os.environ["MODEL_CONTEXT_WINDOW"] = text
        logger.info("🔧 [context_budget] 从 config llm.%s 设置 MODEL_CONTEXT_WINDOW=%s", key, text)
        return int(text)
    return None


def configure_token_counter(llm_config: Optional[Dict[str, Any]] = None) -> None:
    """Expose tokenizer config as env vars used by ContextBudgetEstimator."""
    cfg = llm_config or {}

    if not os.getenv("AIOPS_TOKENIZER_JSON_PATH", "").strip():
        value = cfg.get("tokenizer_json_path") or cfg.get("tokenizer_path")
        if value and str(value).strip():
            os.environ["AIOPS_TOKENIZER_JSON_PATH"] = str(value).strip()
            logger.info("🔧 [context_budget] 从 config 设置 AIOPS_TOKENIZER_JSON_PATH")

    if not os.getenv("AIOPS_TIKTOKEN_ENCODING", "").strip():
        value = cfg.get("tiktoken_encoding")
        if value and str(value).strip():
            os.environ["AIOPS_TIKTOKEN_ENCODING"] = str(value).strip()
            logger.info("🔧 [context_budget] 从 config 设置 AIOPS_TIKTOKEN_ENCODING=%s", value)


class ThinkStreamFilter:
    """Controls visible streaming of model `<think>` content."""

    VALID_MODES = {"full", "truncated", "hidden"}

    def __init__(self, mode: str = "full", max_chars: int = 1200):
        normalized = (mode or "full").strip().lower()
        self.mode = normalized if normalized in self.VALID_MODES else "full"
        self.max_chars = max(0, int(max_chars or 0))
        self._inside_think = False
        self._think_chars = 0
        self._truncated_current_block = False

    def filter_message(self, text: str) -> str:
        """Filter a complete AI message preview."""
        if self.mode == "full":
            return text or ""

        import re

        if self.mode == "hidden":
            return re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL | re.IGNORECASE)

        def _truncate(match):
            body = match.group(1)
            if len(body) <= self.max_chars:
                return match.group(0)
            return f"<think>{body[:self.max_chars]}\n...（think 已截断）\n</think>"

        return re.sub(r"<think>(.*?)</think>", _truncate, text or "", flags=re.DOTALL | re.IGNORECASE)

    def filter_token(self, text: str) -> str:
        """Filter token streaming while preserving state across chunks."""
        if self.mode == "full":
            return text or ""
        if self.mode == "hidden":
            return self._filter_hidden_token(text)
        return self._filter_truncated_token(text)

    def _filter_hidden_token(self, text: str) -> str:
        remaining = text or ""
        visible = []
        while remaining:
            if self._inside_think:
                end = remaining.lower().find("</think>")
                if end < 0:
                    return "".join(visible)
                remaining = remaining[end + len("</think>"):]
                self._inside_think = False
                continue

            start = remaining.lower().find("<think>")
            if start < 0:
                visible.append(remaining)
                break
            visible.append(remaining[:start])
            remaining = remaining[start + len("<think>"):]
            self._inside_think = True
        return "".join(visible)

    def _filter_truncated_token(self, text: str) -> str:
        remaining = text or ""
        visible = []
        while remaining:
            if not self._inside_think:
                start = remaining.lower().find("<think>")
                if start < 0:
                    visible.append(remaining)
                    break
                visible.append(remaining[: start + len("<think>")])
                remaining = remaining[start + len("<think>"):]
                self._inside_think = True
                self._think_chars = 0
                self._truncated_current_block = False
                continue

            end = remaining.lower().find("</think>")
            think_part = remaining if end < 0 else remaining[:end]
            remaining_after_end = "" if end < 0 else remaining[end + len("</think>"):]

            if not self._truncated_current_block:
                remaining_budget = self.max_chars - self._think_chars
                if remaining_budget > 0:
                    visible_part = think_part[:remaining_budget]
                    visible.append(visible_part)
                    self._think_chars += len(visible_part)
                if len(think_part) > max(remaining_budget, 0):
                    visible.append("\n...（think 已截断）\n")
                    self._truncated_current_block = True

            if end < 0:
                break

            visible.append("</think>")
            self._inside_think = False
            self._think_chars = 0
            self._truncated_current_block = False
            remaining = remaining_after_end
        return "".join(visible)


class HolmesService:
    """AIOps Copilot 服务类（唯一模式：AICall + Workflow）"""

    def __init__(self):
        """初始化服务"""
        self.config: Optional[AppConfig] = None
        self.runbook_manager = RunbookManager()
        self.merged_catalog: Optional[RunbookCatalog] = None
        self.federation_coordinator: Optional[FederationCoordinator] = None
        self.federation_agent: Optional[FederationAgent] = None
        self._init_lock = threading.Lock()
        self._init_in_progress: bool = False
        self._init_error: Optional[str] = None
        self._init_started_at: Optional[datetime] = None
        self.workflow_config: Dict = {}  # 工作流配置（max_steps 等）
        self.metrics_config: Dict = {}   # 质量指标配置
        self.i18n_config: Dict = {}      # i18n 配置（prompt/response language）
        self.raw_config: Dict = {}       # 完整原始配置
        self.ai_call: Optional[AICall] = None
        self.mcp_tools: list = []

    def _is_initialized(self) -> bool:
        """检查服务是否已初始化"""
        return self.config is not None and self.ai_call is not None

    def initialize(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_steps: int = 50,
        config_file: Optional[Path] = None
    ) -> Tuple[AppConfig, Any]:
        """初始化服务配置和 AICall 实例"""
        if self._is_initialized():
            return self.config, self.ai_call

        with self._init_lock:
            if self._is_initialized():
                return self.config, self.ai_call

            self._init_in_progress = True
            self._init_error = None
            self._init_started_at = datetime.now()

            logger.info("初始化 AIOps Copilot 服务...")

            try:
                project_root = get_project_root()

                if config_file is None:
                    config_file, env_name = get_config_file_path(project_root)
                    logger.info(f"🔧 运行环境: {env_name}")

                # 读取原始 YAML
                _raw_config: dict = {}
                if config_file.exists():
                    import yaml as _yaml
                    with open(config_file, "r", encoding="utf-8") as _f:
                        _raw_config = _yaml.safe_load(_f) or {}

                # 环境变量替换
                from app.core.holmes.config_loader import substitute_env_vars
                _raw_config = substitute_env_vars(_raw_config, logger)

                _llm_config = _raw_config.get("llm", {}) or {}
                self.workflow_config = _raw_config.get("workflow", {}) or {}
                self.metrics_config = _raw_config.get("metrics", {}) or {}
                self.i18n_config = _raw_config.get("i18n", {}) or {}
                self.raw_config = _raw_config

                from app.core.workflow.metrics import load_metrics_config
                load_metrics_config(self.metrics_config)

                # API Key 优先级: 参数 > 环境变量 > config
                final_api_key = (
                    api_key
                    or os.getenv("LLM_API_KEY")
                    or _llm_config.get("api_key")
                    or os.getenv("DEEPSEEK_API_KEY")
                    or os.getenv("OPENAI_API_KEY")
                )
                if not final_api_key:
                    raise ValueError(
                        "未提供 API Key，请通过 Secret LLM_API_KEY 或 config.yaml llm.api_key 设置"
                    )

                final_model = (
                    model
                    or os.getenv("LLM_MODEL")
                    or _llm_config.get("model")
                    or "deepseek/deepseek-chat"
                )
                if not final_model.strip():
                    final_model = _llm_config.get("model") or "deepseek/deepseek-chat"

                final_api_base = os.getenv("LLM_API_BASE") or _llm_config.get("api_base") or None
                if final_api_base is not None and not final_api_base.strip():
                    final_api_base = None

                configure_model_context_window(_llm_config)
                configure_token_counter(_llm_config)

                # 加载 Holmes Config（仍需用于 runbook catalog）
                if config_file.exists():
                    logger.info(f"从配置文件加载: {config_file}")
                    self.config = load_holmes_config_from_yaml(
                        config_file=config_file,
                        api_key=final_api_key,
                        model=final_model,
                        max_steps=max_steps,
                        api_base=final_api_base,
                        logger=logger,
                    )
                else:
                    logger.warning(f"配置文件不存在: {config_file}，使用默认配置")
                    self.config = AppConfig(
                        llm_model=final_model,
                        llm_api_key=final_api_key,
                        llm_api_base=final_api_base,
                        max_steps=max_steps,
                    )

                # 加载 runbooks
                import time
                step_start = time.time()
                logger.info("🔄 加载 runbook catalogs...")
                self._load_runbooks()
                logger.info(f"   ✅ Runbook 加载完成 ({time.time() - step_start:.2f}s)")

                # 创建 AICall 实例
                step_start = time.time()
                logger.info("🔄 创建 AICall 实例 (LangGraph)...")
                summary_mode, summary_max_chars = self.get_observation_summary_config()
                self.ai_call = AICall(
                    model=final_model,
                    api_key=final_api_key,
                    api_base=final_api_base or "",
                    observation_summary_mode=summary_mode,
                    observation_summary_max_chars=summary_max_chars,
                    context_compaction_config=self.get_context_compaction_config(),
                    chat_model_extra_body=self.get_chat_model_extra_body_config(_llm_config),
                )
                logger.info("   ✅ AICall 实例创建完成 (model=%s, observation_summary=%s/%d, %.2fs)",
                           final_model, summary_mode, summary_max_chars, time.time() - step_start)

                # 加载 MCP 工具
                mcp_cfg = _raw_config.get("mcp_servers", {})
                if mcp_cfg:
                    import asyncio
                    import concurrent.futures
                    from app.core.aicall.tools import load_mcp_tools
                    try:
                        step_start = time.time()
                        logger.info("🔄 [AICall] 加载 MCP 工具...")
                        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                            self.mcp_tools = pool.submit(
                                lambda cfg=mcp_cfg: asyncio.run(load_mcp_tools(cfg))
                            ).result(timeout=60)
                        logger.info("   ✅ [AICall] MCP 工具加载完成: %d 个 (%.2fs)",
                                   len(self.mcp_tools), time.time() - step_start)
                        for t in self.mcp_tools:
                            logger.debug("      📡 %s", t.name)
                    except Exception as e:
                        logger.error("   ❌ [AICall] MCP 工具加载失败: %s", e, exc_info=True)
                        self.mcp_tools = []
                else:
                    self.mcp_tools = []
                    logger.info("   ℹ️ [AICall] 无 MCP 服务器配置")

                # 加载内置工具
                from app.core.aicall.builtin_tools import get_builtin_tools
                builtin = get_builtin_tools()
                self.mcp_tools = self.mcp_tools + builtin
                logger.info("   🔧 [AICall] 工具总计: %d 个 (MCP %d + 内置 %d)",
                           len(self.mcp_tools), len(self.mcp_tools) - len(builtin), len(builtin))

                # 初始化联邦协调器
                _federation_cfg = _raw_config.get("federation", {})
                if _federation_cfg.get("enabled", False):
                    self.federation_coordinator = get_federation_coordinator(
                        federation_config=_federation_cfg,
                        model=final_model,
                        api_key=final_api_key,
                        api_base=final_api_base,
                    )
                    if self.federation_coordinator:
                        logger.info("[FEDERATION] 联邦协调器初始化完成")
                    self.federation_agent = get_federation_agent(
                        federation_config=_federation_cfg,
                        model=final_model,
                        api_key=final_api_key,
                        api_base=final_api_base,
                    )
                    if self.federation_agent:
                        logger.info("[FEDERATION] FederationAgent 初始化完成")
                else:
                    logger.debug("[FEDERATION] federation 未启用，跳过")

                logger.info("✅ 服务初始化完成 | 模式=AICall(LangGraph) | 模型=%s",
                           self.config.model)

                # 输出资源信息
                step_start = time.time()
                self._log_loaded_resources()
                logger.info(f"   ✅ 资源信息输出完成 ({time.time() - step_start:.2f}s)")

                # 禁用不可用的工具
                self._disable_tools(["kubectl_top_nodes", "kubectl_top_pods"])

                return self.config, self.ai_call
            except Exception as e:
                self._init_error = str(e)
                raise
            finally:
                self._init_in_progress = False

    def _disable_tools(self, tool_names: list):
        """从工具列表中移除指定工具"""
        if self.ai_call and self.mcp_tools:
            before = len(self.mcp_tools)
            self.mcp_tools = [t for t in self.mcp_tools if t.name not in tool_names]
            removed = before - len(self.mcp_tools)
            if removed:
                logger.info("⛔ [AICall] 已禁用 %d 个工具: %s", removed, tool_names)

    def get_node_max_steps(self, node_id: str) -> int:
        """获取节点 max_steps，优先级: 环境变量 > config.yaml > 默认值"""
        defaults = {"layer": 3, "evidence": 10, "rca": 8, "conclusion": 3}
        env_key = f"WORKFLOW_MAX_STEPS_{node_id.upper()}"
        env_val = os.getenv(env_key)
        if env_val and env_val.isdigit():
            return int(env_val)
        config_val = self.workflow_config.get("max_steps", {}).get(node_id)
        if config_val is not None:
            return int(config_val)
        return defaults.get(node_id, 10)

    def _build_request_scoped_ai_call(self) -> Optional[AICall]:
        """为单次 workflow 请求创建独立的 AICall 实例，避免并发共享底层 LLM 客户端。"""
        if self.ai_call is None:
            return None

        from app.core.aicall.client import AICall
        summary_mode, summary_max_chars = self.get_observation_summary_config()

        try:
            return AICall(
                model=self.ai_call.model_str,
                api_key=self.ai_call.api_key,
                api_base=self.ai_call.api_base,
                observation_summary_mode=summary_mode,
                observation_summary_max_chars=summary_max_chars,
                context_compaction_config=self.get_context_compaction_config(),
                chat_model_extra_body=self.get_chat_model_extra_body_config(),
            )
        except TypeError:
            # Unit-test fakes may not implement the production constructor extension.
            return AICall(
                model=self.ai_call.model_str,
                api_key=self.ai_call.api_key,
                api_base=self.ai_call.api_base,
            )

    @staticmethod
    def _normalize_language(language: Optional[str], default: str = "zh") -> str:
        """标准化语言标识，仅支持 zh / en。"""
        value = str(language or default or "zh").strip().lower()
        if value.startswith("en"):
            return "en"
        if value.startswith("zh"):
            return "zh"
        return default

    def get_prompt_language(self) -> str:
        """获取 workflow prompt 语言，优先级: 环境变量 > config.yaml > 默认值 zh"""
        env_val = os.getenv("PROMPT_LANGUAGE")
        if env_val:
            return self._normalize_language(env_val)
        return self._normalize_language(self.i18n_config.get("prompt_language"), default="zh")

    def get_response_language(self) -> str:
        """获取最终报告语言，优先级: 环境变量 > config.yaml > 默认值 zh"""
        env_val = os.getenv("RESPONSE_LANGUAGE")
        if env_val:
            return self._normalize_language(env_val)
        return self._normalize_language(self.i18n_config.get("response_language"), default="zh")

    def get_think_stream_config(self) -> Tuple[str, int]:
        """获取 `<think>` 流式展示配置。

        mode:
        - full: 完整展示（默认）
        - truncated: 只展示前 N 字符
        - hidden: 不展示
        """
        think_cfg = self.workflow_config.get("think_stream", {}) if isinstance(self.workflow_config, dict) else {}
        if not isinstance(think_cfg, dict):
            think_cfg = {}
        mode = (
            os.getenv("AIOPS_THINK_STREAM_MODE")
            or os.getenv("THINK_STREAM_MODE")
            or think_cfg.get("mode")
            or "full"
        )
        max_chars_raw = (
            os.getenv("AIOPS_THINK_STREAM_MAX_CHARS")
            or os.getenv("THINK_STREAM_MAX_CHARS")
            or think_cfg.get("max_chars")
            or 1200
        )
        try:
            max_chars = int(max_chars_raw)
        except (TypeError, ValueError):
            max_chars = 1200
        return str(mode), max_chars

    def get_observation_summary_config(self) -> Tuple[str, int]:
        """获取工具 observation 摘要策略。

        mode:
        - rule: 默认，规则摘要优先，超长才 LLM 兜底
        - ai: 每次工具 observation 都强制调用 LLM summarizer

        配置唯一来源是 config.yaml 的 workflow.observation_summary。
        Secret 只承载模型连接和敏感信息，避免 Secret 环境变量覆盖 ConfigMap 造成实际模式不透明。
        """
        wf_cfg = self.workflow_config if isinstance(self.workflow_config, dict) else {}
        obs_cfg = wf_cfg.get("observation_summary", {}) if isinstance(wf_cfg.get("observation_summary", {}), dict) else {}
        mode = obs_cfg.get("mode") or "rule"
        normalized_mode = str(mode or "rule").strip().lower()
        if normalized_mode not in {"rule", "ai"}:
            normalized_mode = "rule"

        max_chars_raw = obs_cfg.get("max_chars") or 3000
        try:
            max_chars = int(max_chars_raw)
        except (TypeError, ValueError):
            max_chars = 3000
        return normalized_mode, max(200, max_chars)

    def get_context_compaction_config(self) -> Dict[str, Any]:
        """获取运行时上下文压缩配置。

        仅从 config.yaml 的 workflow.context_compaction 读取，避免环境变量
        隐式改变模型上下文治理行为。
        """
        wf_cfg = self.workflow_config if isinstance(self.workflow_config, dict) else {}
        cfg = wf_cfg.get("context_compaction", {}) if isinstance(wf_cfg.get("context_compaction", {}), dict) else {}
        result: Dict[str, Any] = {
            "enabled": bool(cfg.get("enabled", True)),
            "nodes": cfg.get("nodes") or ["evidence"],
            "max_context_window": cfg.get("max_context_window") or 35000,
            "trigger_ratio": cfg.get("trigger_ratio") or 0.70,
            "max_compactions_per_call": cfg.get("max_compactions_per_call") or 1,
            "summary_max_tokens": cfg.get("summary_max_tokens") or 1200,
        }
        if isinstance(result["nodes"], str):
            result["nodes"] = [result["nodes"]]
        try:
            result["max_context_window"] = int(result["max_context_window"])
        except (TypeError, ValueError):
            result["max_context_window"] = 35000
        try:
            result["trigger_ratio"] = float(result["trigger_ratio"])
        except (TypeError, ValueError):
            result["trigger_ratio"] = 0.70
        try:
            result["max_compactions_per_call"] = int(result["max_compactions_per_call"])
        except (TypeError, ValueError):
            result["max_compactions_per_call"] = 1
        try:
            result["summary_max_tokens"] = int(result["summary_max_tokens"])
        except (TypeError, ValueError):
            result["summary_max_tokens"] = 1200
        return result

    def get_chat_model_extra_body_config(
        self,
        llm_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Return provider-specific ChatOpenAI extra_body options.

        This is a transport/model-control boundary only. Workflow nodes should
        not know provider-specific options such as local Qwen thinking controls.
        """
        cfg = llm_config if isinstance(llm_config, dict) else None
        if cfg is None:
            raw_cfg = getattr(self, "raw_config", {}) if isinstance(getattr(self, "raw_config", {}), dict) else {}
            cfg = raw_cfg.get("llm", {}) if isinstance(raw_cfg.get("llm", {}), dict) else {}
        extra_body = cfg.get("extra_body", {}) if isinstance(cfg.get("extra_body", {}), dict) else {}
        return dict(extra_body)

    def _load_runbooks(self):
        """加载和合并 runbook catalogs"""
        custom_catalog = self.runbook_manager.load_custom_catalog()
        base_catalog = self.config.get_runbook_catalog()
        self.merged_catalog = self.runbook_manager.merge_catalogs(
            base_catalog, custom_catalog
        )

    def _log_loaded_resources(self):
        """输出加载的资源信息（按 MCP Server 分组，INFO 级别可见）"""
        logger.info("=" * 50)
        logger.info("📋 [AICall] 资源概览")
        logger.info("=" * 50)

        mcp_tools = [t for t in self.mcp_tools if not getattr(t, '_is_builtin', False)]
        builtin_tools = [t for t in self.mcp_tools if getattr(t, '_is_builtin', False)]

        # 按 MCP Server 分组
        server_groups: dict = {}
        ungrouped = []
        for t in mcp_tools:
            srv = (getattr(t, 'server_name', None)
                   or (getattr(t, 'metadata', {}) or {}).get('server_name')
                   or (getattr(t, 'metadata', {}) or {}).get('server'))
            if srv:
                server_groups.setdefault(srv, []).append(t)
            else:
                ungrouped.append(t)

        logger.info("   🔧 工具总计: %d 个 (MCP %d + 内置 %d)",
                    len(self.mcp_tools), len(mcp_tools), len(builtin_tools))
        logger.info("-" * 50)

        if server_groups:
            for srv_name, tools in server_groups.items():
                logger.info("   📡 [%s] %d 个工具:", srv_name, len(tools))
                for t in tools:
                    logger.info("      - %s", t.name)
                    logger.debug("        描述: %s", getattr(t, 'description', '')[:120])
        if ungrouped:
            logger.info("   📡 [MCP] %d 个工具:", len(ungrouped))
            for t in ungrouped:
                logger.info("      - %s", t.name)
                logger.debug("        描述: %s", getattr(t, 'description', '')[:120])

        if builtin_tools:
            logger.info("   🔧 [内置] %d 个工具:", len(builtin_tools))
            for t in builtin_tools:
                logger.info("      - %s", t.name)

        if self.merged_catalog:
            catalog_entries = getattr(self.merged_catalog, 'catalog', [])
            count = len(catalog_entries) if catalog_entries else 0
            logger.info("   📚 Runbooks: %d 个", count)
            if catalog_entries:
                for entry in catalog_entries:
                    rb_id = getattr(entry, 'id', '') or entry.get('id', '') if isinstance(entry, dict) else getattr(entry, 'id', '')
                    rb_desc = getattr(entry, 'description', '') or (entry.get('description', '') if isinstance(entry, dict) else '')
                    logger.info("      - [%s] %s", rb_id, rb_desc[:60])
        logger.info("=" * 50)

    def execute_query(
        self,
        question: str,
        system_prompt: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_steps: int = 50,
        workflow_overrides: Optional[Dict[str, Any]] = None,
        workflow_title: str = "工作流诊断模式",
    ) -> dict:
        """执行查询并返回结果（收集流式工作流输出为完整文本）"""
        start_time = datetime.now()
        try:
            if api_key or model or max_steps != 50:
                self.config = None
                self.ai_call = None
            self.initialize(api_key=api_key, model=model, max_steps=max_steps)

            import time
            max_wait = 60
            waited = 0
            while not self._is_initialized() and waited < max_wait:
                if waited == 0:
                    logger.info("⏳ 等待服务初始化完成...")
                time.sleep(1)
                waited += 1

            if not self._is_initialized():
                return {
                    "success": False,
                    "error": "服务初始化超时或失败",
                    "execution_time": (datetime.now() - start_time).total_seconds(),
                    "timestamp": datetime.now().isoformat()
                }

            if waited > 0:
                logger.info(f"✅ 初始化完成（等待了 {waited}s）")

            logger.info(f"执行查询: {question[:100]}...")

            chunks = []
            for chunk in self.execute_query_stream(
                question=question,
                max_steps=max_steps,
                output_format="text",
                workflow_overrides=workflow_overrides,
                workflow_title=workflow_title,
            ):
                chunks.append(chunk)
            full_text = "".join(chunks)
            return {
                "success": True,
                "result": full_text,
                "tool_calls": [],
            }
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"执行查询时出错: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }

    def execute_query_stream(
        self,
        question: str,
        system_prompt: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_steps: int = 50,
        output_format: str = "text",
        cancel_event: Optional[Any] = None,
        workflow_overrides: Optional[Dict[str, Any]] = None,
        workflow_title: str = "工作流诊断模式",
    ) -> Generator[str, None, None]:
        """执行查询并以流式方式返回结果"""
        import time
        max_wait = 60
        waited = 0
        while not self._is_initialized() and waited < max_wait:
            if waited == 0:
                logger.info("⏳ 等待服务初始化完成...")
            time.sleep(1)
            waited += 1

        if not self._is_initialized():
            error_msg = "服务初始化超时或失败"
            logger.error(error_msg)
            if output_format == "text":
                yield f"❌ {error_msg}\n"
            else:
                yield create_sse_message_cn("error", {"error": error_msg})
            return

        if waited > 0:
            logger.info(f"✅ 初始化完成（等待了 {waited}s）")

        logger.info("🔄 使用工作流模式执行查询")
        yield from self._execute_query_stream_workflow(
            question=question,
            output_format=output_format,
            cancel_event=cancel_event,
            workflow_overrides=workflow_overrides,
            workflow_title=workflow_title,
        )

    def _execute_query_stream_workflow(
        self,
        question: str,
        output_format: str = "sse",
        cancel_event: Optional[Any] = None,
        workflow_overrides: Optional[Dict[str, Any]] = None,
        workflow_title: str = "工作流诊断模式",
    ) -> Generator[str, None, None]:
        """使用工作流模式执行查询，支持 text 和 sse 两种输出格式"""
        try:
            from app.core.workflow.executor import WorkflowExecutor

            executor = WorkflowExecutor(holmes_service=self)
            executor.ai_call = self._build_request_scoped_ai_call()
            executor.mcp_tools = self.mcp_tools or []
            logger.debug("🔀 [Workflow] aicall 路径激活 | tools=%d", len(executor.mcp_tools))

            if output_format == "text":
                yield from self._workflow_to_text(
                    executor,
                    question,
                    cancel_event=cancel_event,
                    workflow_overrides=workflow_overrides,
                    workflow_title=workflow_title,
                )
                return

            # SSE 格式输出
            stream_kwargs = {"cancel_event": cancel_event}
            try:
                import inspect

                if "workflow_overrides" in inspect.signature(executor.execute_stream).parameters:
                    stream_kwargs["workflow_overrides"] = workflow_overrides
            except (TypeError, ValueError):
                stream_kwargs["workflow_overrides"] = workflow_overrides

            for event in executor.execute_stream(question, **stream_kwargs):
                event_type = event.get("type", "unknown")
                payload = {k: v for k, v in event.items() if k != "type"}
                yield create_sse_message_cn(event_type, payload)

        except ImportError as e:
            logger.error(f"工作流模块导入失败: {e}")
            if output_format == "text":
                yield f"❌ 工作流模块导入失败: {e}\n"
            else:
                yield create_sse_message_cn("error", {
                    "error": f"工作流模块未安装或导入失败: {str(e)}",
                    "suggestion": "请确保已安装 langgraph: pip install langgraph"
                })
        except Exception as e:
            logger.error(f"工作流执行失败: {e}", exc_info=True)
            if output_format == "text":
                yield f"❌ 工作流执行失败: {e}\n"
            else:
                yield create_sse_message_cn("error", {
                    "error": f"工作流执行失败: {str(e)}"
                })

    def _workflow_to_text(
        self,
        executor: Any,
        question: str,
        cancel_event: Optional[Any] = None,
        workflow_overrides: Optional[Dict[str, Any]] = None,
        workflow_title: str = "工作流诊断模式",
    ) -> Generator[str, None, None]:
        """工作流执行结果转换为美观的文本格式，专为终端 curl 优化"""
        import json

        def emit(text: str) -> str:
            return text + "\n"

        def format_layer_node_output(snapshot: dict) -> str:
            lines = []
            layer = snapshot.get("layer", "?")
            conf = snapshot.get("layer_confidence", 0) or 0
            layer_reasoning = snapshot.get("layer_reasoning", "")
            lines.append(f"**层级**: {layer}")
            lines.append(f"**置信度**: {conf:.0%}")
            if layer_reasoning:
                lines.append(f"**判定理由**: {layer_reasoning}")
            return "\n".join(lines)

        def format_evidence_node_output(snapshot: dict) -> str:
            lines = []
            count = snapshot.get("evidence_count", 0)
            collected = snapshot.get("collected_count", 0)
            completeness = snapshot.get("completeness", 0) or 0
            lines.append(f"**证据数量**: {count}")
            lines.append(f"**已采集**: {collected}")
            lines.append(f"**完整度**: {completeness:.0%}")
            return "\n".join(lines)

        def format_rca_node_output(snapshot: dict) -> str:
            lines = []
            root_cause = snapshot.get("root_cause", "")
            conf = snapshot.get("confidence")
            conf_str = f"{conf:.0%}" if conf else "?"
            lines.append(f"**根因**: {root_cause}")
            lines.append(f"**置信度**: {conf_str}")
            return "\n".join(lines)

        yield emit("=" * 70)
        yield emit(f"🔄 K8s AIOps Copilot - {workflow_title}")
        yield emit("=" * 70)
        yield emit("")

        question_display = question[:100] if len(question) > 100 else question
        yield emit(f"📝 问题: {question_display}")
        yield emit("")
        yield emit("-" * 70)

        final_answer = ""
        final_report_emitted = False
        metrics_data = None
        _token_streaming_active = False
        _token_stream_buffer = ""
        think_mode, think_max_chars = self.get_think_stream_config()
        think_filter = ThinkStreamFilter(think_mode, think_max_chars)
        logger.info("🧠 think stream mode=%s max_chars=%d", think_filter.mode, think_filter.max_chars)
        node_outputs = {"layer": "", "evidence": "", "rca": "", "conclusion": ""}

        for event in executor.execute_stream(
            question,
            cancel_event=cancel_event,
            workflow_overrides=workflow_overrides,
        ):
            event_type = event.get("type", "unknown")

            if event_type == "run_start":
                run_id = event.get("run_id", "?")
                yield emit(f"🚀 开始诊断 [run_id: {run_id}]")
                yield emit("")

            elif event_type == "node_start":
                node_name = event.get("node_name", event.get("node", "?"))
                yield emit(f"📍 [{node_name}] 执行中...")

            elif event_type == "thinking":
                node_name = event.get("node_name", "?")
                think_type = event.get("thinking_type", event.get("type", ""))
                if think_type == "tool_start":
                    yield emit(f"   💭 [{node_name}] 调用工具: {event.get('tool_name')}")
                elif think_type == "tool_result":
                    yield emit(f"   💭 [{node_name}] 工具结果: {event.get('tool_name')} ({event.get('status')})")
                    preview = event.get("result_preview", "")
                    if preview:
                        yield emit(f"      📄 {preview[:300]}{'...' if len(preview) > 300 else ''}")
                elif think_type == "ai_message":
                    raw_content = event.get("full_content") or event.get("content") or ""
                    content = think_filter.filter_message(raw_content).strip()
                    if _token_streaming_active:
                        yield "\n"
                        _token_streaming_active = False
                        if content == _token_stream_buffer.strip():
                            _token_stream_buffer = ""
                            continue
                        _token_stream_buffer = ""
                    if content:
                        yield emit(f"   💭 [{node_name}] AI: {content[:500]}")
                elif think_type == "ai_token":
                    token_text = think_filter.filter_token(event.get("content", ""))
                    if token_text:
                        if not _token_streaming_active:
                            yield f"   💭 [{node_name}] "
                            _token_streaming_active = True
                            _token_stream_buffer = ""
                        _token_stream_buffer += token_text
                        yield token_text
                elif think_type == "iteration_end":
                    yield emit(f"   💭 [{node_name}] 迭代 #{event.get('iteration')} 完成")

            elif event_type == "heartbeat":
                node_name = event.get("node_name", event.get("node", "?"))
                yield emit(f"   ⏳ [{node_name}] 仍在处理，等待工具或模型返回...")

            elif event_type == "node_complete":
                node_name = event.get("node_name", event.get("node", "?"))
                duration = event.get("duration_seconds", 0)
                snapshot = event.get("state_snapshot", {})

                yield emit(f"   ✅ [{node_name}] 完成 ({format_duration(duration)})")

                handoff = event.get("handoff_summary", "")
                if handoff:
                    yield emit(f"   📤 → 下游数据: {handoff}")
                yield emit("")

                node_id = event.get("node", "")
                if node_id == "layer":
                    yield emit("   ┌──────────────────────────────────────────┐")
                    yield emit("   │ 📊 问题定位结果                              │")
                    yield emit("   └──────────────────────────────────────────┘")
                    yield emit("")
                    layer = snapshot.get("layer", "?")
                    layers = snapshot.get("layers", [])
                    conf = snapshot.get("layer_confidence", 0) or 0
                    if layers and len(layers) > 1:
                        yield emit(f"   层级: {' + '.join(layers)}（主层级: {layer}）")
                    else:
                        yield emit(f"   层级: {layer}")
                    yield emit(f"   置信度: {conf:.0%}")
                    node_outputs["layer"] = snapshot.get("layer_analysis", "") or format_layer_node_output(snapshot)

                elif node_id == "evidence":
                    yield emit("   ┌──────────────────────────────────────────┐")
                    yield emit("   │ 🔍 证据采集结果                              │")
                    yield emit("   └──────────────────────────────────────────┘")
                    yield emit("")
                    count = snapshot.get("evidence_count", 0)
                    collected = snapshot.get("collected_count", 0)
                    completeness = snapshot.get("completeness", 0) or 0
                    yield emit(f"   证据: {collected}/{count} 项, 完整度: {completeness:.0%}")
                    plan_output = format_evidence_plan_output(snapshot.get("evidence_analysis", ""))
                    if plan_output:
                        yield emit("")
                        yield emit(plan_output)
                    node_outputs["evidence"] = snapshot.get("evidence_analysis", "") or format_evidence_node_output(snapshot)

                elif node_id == "rca":
                    yield emit("   ┌──────────────────────────────────────────┐")
                    yield emit("   │ 🎯 根因分析结果                              │")
                    yield emit("   └──────────────────────────────────────────┘")
                    yield emit("")
                    root_cause = snapshot.get("root_cause", "")
                    conf = snapshot.get("confidence")
                    conf_str = f"{conf:.0%}" if conf else "?"
                    if root_cause:
                        rc_display = root_cause[:150]
                        if len(root_cause) > 150:
                            rc_display += "..."
                        yield emit(f"   根因: {rc_display}")
                    yield emit(f"   置信度: {conf_str}")

                    causal_chain = snapshot.get("causal_chain", {})
                    if causal_chain:
                        yield emit("   🔗 因果链:")
                        trigger = causal_chain.get("trigger") or causal_chain.get("root_cause", "")
                        mechanism = causal_chain.get("mechanism") or causal_chain.get("propagation", "")
                        manifestation = causal_chain.get("manifestation", "")
                        if trigger:
                            yield emit(f"     根本原因: {trigger}")
                        if mechanism:
                            yield emit(f"     传导机制: {mechanism}")
                        if manifestation:
                            yield emit(f"     最终表现: {manifestation}")
                        yield emit("")

                    node_outputs["rca"] = snapshot.get("rca_analysis", "") or format_rca_node_output(snapshot)

                elif node_id == "conclusion":
                    yield emit("   ┌──────────────────────────────────────────┐")
                    yield emit("   │ 📋 汇总总结结果                              │")
                    yield emit("   └──────────────────────────────────────────┘")
                    yield emit("")
                    length = snapshot.get("conclusion_length", 0)
                    yield emit(f"   报告长度: {length} 字符")

                yield emit("")

            elif event_type == "final":
                final_answer = event.get("answer", "")
                metrics_data = event.get("metrics", {})
                elapsed = event.get("elapsed_seconds", 0)
                node_outputs["conclusion"] = final_answer or "（汇总节点生成最终报告）"
                yield emit("-" * 70)
                yield emit(f"📊 诊断完成! 总耗时: {format_duration(elapsed)}")
                yield emit("-" * 70)
                yield emit("")

            elif event_type == "remediation_approval_required":
                if final_answer and not final_report_emitted:
                    yield emit("=" * 70)
                    yield emit("🎯 诊断报告")
                    yield emit("=" * 70)
                    yield emit("")
                    yield emit("## 📋 节点四：汇总总结")
                    yield emit("-" * 70)
                    yield emit(node_outputs["conclusion"])
                    yield emit("")
                    final_report_emitted = True
                yield emit("=" * 70)
                yield emit("🛠️ 修复审批中断")
                yield emit("=" * 70)
                yield emit(f"审批类型: {event.get('approval_kind')}")
                yield emit(f"审批 ID: {event.get('approval_id')}")
                yield emit(f"标题: {event.get('title')}")
                yield emit("请调用:")
                yield emit(
                    "curl -X POST http://<host>/remediation/approve "
                    f"-d run_id={event.get('run_id')} "
                    f"-d approval_id={event.get('approval_id')} "
                    "-d approved=true"
                )
                yield emit("")

            elif event_type == "remediation_tool_result":
                yield emit(
                    f"🛠️ 修复工具结果 [{event.get('stage')}]: "
                    f"{event.get('command')} -> {event.get('status')}"
                )
                preview = event.get("result_preview")
                if preview:
                    yield emit(str(preview)[:500])
                yield emit("")

            elif event_type == "remediation_finished":
                yield emit(
                    f"🛠️ 修复流程结束: {event.get('status')} "
                    f"({event.get('reason', '')})"
                )
                yield emit("")

            elif event_type == "error":
                error = event.get("error", "未知错误")
                yield emit(f"❌ 错误: {error}")
                yield emit("")

        if final_answer and not final_report_emitted:
            yield emit("=" * 70)
            yield emit("🎯 诊断报告")
            yield emit("=" * 70)
            yield emit("")
            if node_outputs["conclusion"]:
                yield emit("## 📋 节点四：汇总总结")
                yield emit("-" * 70)
                yield emit(node_outputs["conclusion"])
                yield emit("")

        yield emit("=" * 70)
        yield emit("✅ 诊断完成!")
        yield emit("=" * 70)

    def get_tools_info(self) -> dict:
        """获取可用工具信息"""
        self.initialize()
        tool_names = [t.name for t in self.mcp_tools]
        return {
            "success": True,
            "total_tools": len(tool_names),
            "tools": sorted(tool_names),
            "toolsets": [{"name": "AICall(LangGraph)", "enabled": True, "status": "active"}],
        }

    def get_tools_detail(self) -> dict:
        """获取更详细的工具信息（面向排障/二次开发）"""
        self.initialize()
        tools_detail = []
        for t in self.mcp_tools:
            d = {"name": t.name}
            desc = getattr(t, 'description', None)
            if desc:
                d["description"] = desc[:200]
            tools_detail.append(d)
        return {
            "success": True,
            "mode": "AICall(LangGraph)",
            "total_tools": len(tools_detail),
            "tools": tools_detail,
            "toolsets": [{"name": "AICall(LangGraph)", "tools": [t.name for t in self.mcp_tools]}],
        }

    def health_check(self) -> dict:
        """健康检查"""
        initialized = self._is_initialized()
        model_name = None
        if self.config is not None:
            model_name = getattr(self.config, "model", None)
        if not model_name and self.ai_call is not None:
            model_name = getattr(self.ai_call, "model_str", None)
        if initialized:
            return {
                "status": "healthy",
                "config_loaded": True,
                "ai_initialized": True,
                "mode": "AICall(LangGraph)",
                "model": model_name,
            }
        if self._init_in_progress:
            return {
                "status": "initializing",
                "config_loaded": self.config is not None,
                "ai_initialized": initialized,
                "model": model_name,
                "started_at": self._init_started_at.isoformat() if self._init_started_at else None,
            }
        if self._init_error:
            return {
                "status": "unhealthy",
                "error": self._init_error
            }
        return {
            "status": "uninitialized",
            "config_loaded": self.config is not None,
            "ai_initialized": initialized,
            "model": model_name,
        }


# 全局服务实例（单例模式）
_global_service: Optional[HolmesService] = None


def get_service() -> HolmesService:
    """获取全局服务实例"""
    global _global_service
    if _global_service is None:
        _global_service = HolmesService()
    return _global_service
