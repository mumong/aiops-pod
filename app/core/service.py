#!/usr/bin/env python3
"""
HolmesGPT Service
负责 HolmesGPT 的初始化、配置和查询执行
"""
import os
import logging
import threading
from pathlib import Path
from typing import Optional, Tuple, Any, Generator, Dict
from datetime import datetime

from rich.console import Console

from holmes.config import Config
from holmes.core.prompt import build_initial_ask_messages
from holmes.plugins.runbooks import RunbookCatalog

from app.core.runbook import RunbookManager
from app.core.paths import get_project_root
from app.core.prompts import SYSTEM_PROMPT
from app.core.environment import get_config_file_path, log_environment_info, get_environment
from app.core.holmes.streaming import create_sse_message_cn, format_duration
from app.core.holmes.introspection import log_loaded_resources
from app.core.holmes.query_stream import execute_query_stream_sse, execute_query_stream_text
from app.core.holmes.config_loader import load_stream_output_flag, load_holmes_config_from_yaml
from app.core.holmes.call_wrapper import call_with_stream
from app.core.mcp.mcp_patch import patch_mcp_toolset
from app.core.holmes.tool_logging_patch import apply_tool_result_logging_patch
from app.core.federation import get_federation_coordinator, FederationCoordinator

logger = logging.getLogger(__name__)

# 在导入后立即应用 MCP 补丁
patch_mcp_toolset()
# 使每次工具调用的输出与错误写入 app 日志，便于调试 MCP
apply_tool_result_logging_patch()


class HolmesService:
    """HolmesGPT 服务类"""
    
    def __init__(self):
        """初始化服务"""
        self.config: Optional[Config] = None
        self.ai: Any = None
        self.console = Console()
        self.runbook_manager = RunbookManager()
        self.merged_catalog: Optional[RunbookCatalog] = None
        self.stream_output: bool = False  # 流式输出配置
        self.federation_coordinator: Optional[FederationCoordinator] = None
        self._init_lock = threading.Lock()
        self._init_in_progress: bool = False
        self._init_error: Optional[str] = None
        self._init_started_at: Optional[datetime] = None
    
    def initialize(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_steps: int = 50,
        config_file: Optional[Path] = None
    ) -> Tuple[Config, Any]:
        """
        初始化 HolmesGPT 配置和 AI 实例
        
        Args:
            api_key: LLM API Key
            model: 使用的模型
            max_steps: 最大执行步数
            config_file: 配置文件路径，如果为 None 则使用默认路径
        
        Returns:
            (config, ai_instance) 元组
        """
        # 如果已经初始化，直接返回
        if self.config is not None and self.ai is not None:
            return self.config, self.ai

        with self._init_lock:
            # 可能在等待锁期间已经初始化
            if self.config is not None and self.ai is not None:
                return self.config, self.ai

            self._init_in_progress = True
            self._init_error = None
            self._init_started_at = datetime.now()

            logger.info("初始化 HolmesGPT 配置...")

            try:
                # 获取项目根目录
                project_root = get_project_root()

                # 获取配置文件路径（自动检测环境）
                if config_file is None:
                    config_file, env_name = get_config_file_path(project_root)
                    logger.info(f"🔧 运行环境: {env_name}")

                # 先读取流式输出配置（在 Config.load_from_file 之前，避免验证错误）
                if config_file.exists():
                    self.stream_output = load_stream_output_flag(config_file, logger)
                else:
                    self.stream_output = False

                # 读取原始 YAML 用于联邦配置（在 holmes.Config 加载之前）
                _raw_config: dict = {}
                if config_file.exists():
                    import yaml as _yaml
                    with open(config_file, "r", encoding="utf-8") as _f:
                        _raw_config = _yaml.safe_load(_f) or {}

                # 确定使用的 API Key
                final_api_key = api_key or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
                if not final_api_key:
                    raise ValueError(
                        "未提供 API Key，请通过参数或环境变量 DEEPSEEK_API_KEY/OPENAI_API_KEY 设置"
                    )

                # 确定使用的模型
                # 优先级: 参数 > 环境变量 DEEPSEEK_MODEL > 默认值
                env_model = os.getenv("DEEPSEEK_MODEL")
                if env_model and not env_model.startswith("deepseek/"):
                    # LiteLLM 需要 deepseek/ 前缀
                    env_model = f"deepseek/{env_model}"
                final_model = model or env_model or "deepseek/deepseek-chat"

                # 加载配置（需要先创建一个临时配置文件，移除 stream_output 字段）
                if config_file.exists():
                    logger.info(f"从配置文件加载: {config_file}")
                    self.config = load_holmes_config_from_yaml(
                        config_file=config_file,
                        api_key=final_api_key,
                        model=final_model,
                        max_steps=max_steps,
                        logger=logger,
                    )
                else:
                    logger.warning(f"配置文件不存在: {config_file}，使用默认配置")
                    self.config = Config(
                        api_key=final_api_key,
                        model=final_model,
                        max_steps=max_steps
                    )

                # 加载和合并 runbook catalogs
                import time
                step_start = time.time()
                logger.info("🔄 加载 runbook catalogs...")
                self._load_runbooks()
                logger.info(f"   ✅ Runbook 加载完成 ({time.time() - step_start:.2f}s)")

                # 创建 AI 实例
                step_start = time.time()
                logger.info("🔄 创建 AI 实例...")
                logger.info("   📍 调用 config.create_console_toolcalling_llm()...")
                
                self.ai = self.config.create_console_toolcalling_llm()
                
                logger.info(f"   ✅ AI 实例创建完成 ({time.time() - step_start:.2f}s)")

                # 初始化联邦协调器（如配置了 federation.enabled=true）
                _federation_cfg = _raw_config.get("federation", {})
                if _federation_cfg.get("enabled", False):
                    self.federation_coordinator = get_federation_coordinator(
                        federation_config=_federation_cfg,
                        model=final_model,
                        api_key=final_api_key,
                    )
                    if self.federation_coordinator:
                        logger.info("[FEDERATION] 联邦协调器初始化完成")
                else:
                    logger.debug("[FEDERATION] federation 未启用，跳过")

                # 配置自定义 runbook 搜索路径
                step_start = time.time()
                logger.info("🔄 配置 runbook 搜索路径...")
                if self.runbook_manager.runbook_dir.exists():
                    self.runbook_manager.configure_search_path(self.ai)
                logger.info(f"   ✅ 搜索路径配置完成 ({time.time() - step_start:.2f}s)")

                logger.info(f"✅ HolmesGPT 初始化完成，模型: {self.config.model}")
                logger.info(f"📡 输出模式: {'流式输出 (stream)' if self.stream_output else '非流式输出 (invoke)'}")

                # 输出加载的资源信息
                step_start = time.time()
                logger.info("🔄 输出资源信息...")
                self._log_loaded_resources()
                logger.info(f"   ✅ 资源信息输出完成 ({time.time() - step_start:.2f}s)")

                return self.config, self.ai
            except Exception as e:
                self._init_error = str(e)
                raise
            finally:
                self._init_in_progress = False
    
    def _call_with_stream(self, messages: list) -> Any:
        """兼容层：内部委托给 app.core.holmes.call_wrapper.call_with_stream"""
        return call_with_stream(self.ai, messages, logger_override=logger)
    
    def _load_runbooks(self):
        """加载和合并 runbook catalogs"""
        # 加载自定义 runbook catalog
        custom_catalog = self.runbook_manager.load_custom_catalog()
        
        # 获取内置 runbook catalog
        base_catalog = self.config.get_runbook_catalog()
        
        # 合并 catalogs
        self.merged_catalog = self.runbook_manager.merge_catalogs(
            base_catalog, custom_catalog
        )
    
    def _log_loaded_resources(self):
        """输出加载的资源信息（工具集、MCP 服务器、工具、Runbook）"""
        log_loaded_resources(ai=self.ai, merged_catalog=self.merged_catalog, logger=logger)
    
    def execute_query(
        self,
        question: str,
        system_prompt: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_steps: int = 50
    ) -> dict:
        """
        执行查询并返回结果
        
        Args:
            question: 用户问题
            system_prompt: 自定义系统提示词
            api_key: LLM API Key
            model: 使用的模型
            max_steps: 最大执行步数
        
        Returns:
            包含查询结果的字典
        """
        start_time = datetime.now()
        
        try:
            # 如果参数变化，重新初始化
            if api_key or model or max_steps != 50:
                self.config = None
                self.ai = None
            
            # 初始化（如果还未初始化）
            self.initialize(api_key=api_key, model=model, max_steps=max_steps)
            
            # 等待初始化完成（最多60秒）
            import time
            max_wait = 60
            waited = 0
            while (self.config is None or self.ai is None) and waited < max_wait:
                if waited == 0:
                    logger.info("⏳ 等待 HolmesGPT 初始化完成...")
                time.sleep(1)
                waited += 1
            
            if self.config is None or self.ai is None:
                return {
                    "success": False,
                    "error": "HolmesGPT 初始化超时或失败",
                    "execution_time": (datetime.now() - start_time).total_seconds(),
                    "timestamp": datetime.now().isoformat()
                }
            
            if waited > 0:
                logger.info(f"✅ 初始化完成（等待了 {waited}s）")
            
            # 使用系统提示词
            final_system_prompt = system_prompt or SYSTEM_PROMPT
            
            logger.info(f"执行查询: {question[:100]}...")
            
            # 使用合并后的 runbook catalog
            runbook_catalog = (
                self.merged_catalog if self.merged_catalog 
                else self.config.get_runbook_catalog()
            )
            
            # 构建消息
            messages = build_initial_ask_messages(
                console=self.console,
                initial_user_prompt=question,
                file_paths=None,
                tool_executor=self.ai.tool_executor,
                runbooks=runbook_catalog,
                system_prompt_additions=final_system_prompt if final_system_prompt else None
            )
            
            # 根据配置选择调用方式
            if self.stream_output:
                response = self._call_with_stream(messages)
            else:
                response = self.ai.call(messages)
            
            # 提取工具调用信息，并输出调试日志（便于排障）
            tool_calls = []
            if response and hasattr(response, "tool_calls") and response.tool_calls:
                raw_tool_calls = response.tool_calls
                if isinstance(raw_tool_calls, list) and raw_tool_calls:
                    if isinstance(raw_tool_calls[0], dict):
                        tool_calls = raw_tool_calls  # 已经是 dict 列表
                    else:
                        for tool in raw_tool_calls:
                            tool_calls.append(
                                {
                                    "tool_name": getattr(tool, "tool_name", getattr(tool, "name", None)),
                                    "result": str(getattr(tool, "result", None)) if hasattr(tool, "result") else None,
                                    "error": str(getattr(tool, "error", None))
                                    if hasattr(tool, "error") and getattr(tool, "error", None)
                                    else None,
                                }
                            )

            # 日志中打印每一次工具调用的结果预览和错误，方便排障
            if tool_calls:
                logger.info(f"🔧 本次查询共调用 {len(tool_calls)} 个工具（同步模式）:")
                for idx, tc in enumerate(tool_calls, start=1):
                    name = tc.get("tool_name") or tc.get("name") or f"tool_{idx}"
                    result_text = tc.get("result") or ""
                    error_text = tc.get("error") or ""

                    preview = result_text[:500].replace("\n", " ") if result_text else ""
                    logger.info(f"   #{idx} 工具: {name}")
                    if preview:
                        logger.info(f"      📄 结果预览: {preview}{'... (已截断)' if len(result_text) > 500 else ''}")
                    else:
                        logger.info("      📄 结果预览: <空结果>")

                    if error_text:
                        logger.error(f"      ⚠️ 错误: {error_text}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "result": response.result if response else None,
                "tool_calls": tool_calls,
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
        output_format: str = "text"
    ) -> Generator[str, None, None]:
        """
        执行查询并以流式方式返回结果（带耗时统计）
        
        Args:
            question: 用户问题
            system_prompt: 自定义系统提示词
            api_key: LLM API Key
            model: 使用的模型
            max_steps: 最大执行步数
            output_format: 输出格式 - "text"=易读纯文本, "sse"=JSON格式SSE事件
        
        Yields:
            根据 output_format 返回纯文本或 SSE 格式的事件字符串
        """
        # 等待初始化完成（最多60秒）
        import time
        max_wait = 60
        waited = 0
        while (self.config is None or self.ai is None) and waited < max_wait:
            if waited == 0:
                logger.info("⏳ 等待 HolmesGPT 初始化完成...")
            time.sleep(1)
            waited += 1
        
        if self.config is None or self.ai is None:
            error_msg = "HolmesGPT 初始化超时或失败"
            logger.error(error_msg)
            if output_format == "text":
                yield f"❌ {error_msg}\n"
            else:
                from app.core.holmes.streaming import create_sse_message_cn
                yield create_sse_message_cn("error", {"error": error_msg})
            return
        
        if waited > 0:
            logger.info(f"✅ 初始化完成（等待了 {waited}s）")
        
        # 检查是否启用工作流模式
        # 配置方式: 在 deploy/secrets/core.yaml 中设置 USE_WORKFLOW: "true"
        use_workflow = os.getenv("USE_WORKFLOW", "false").lower() in ("true", "1", "yes")
        
        if use_workflow:
            # 工作流模式（POC）
            logger.info("🔄 使用工作流模式执行查询")
            yield from self._execute_query_stream_workflow(
                question=question,
                output_format=output_format
            )
            return
        
        # 原有模式（HolmesGPT agentic loop）
        if output_format == "text":
            yield from execute_query_stream_text(self, question, system_prompt, api_key, model, max_steps)
            return

        yield from execute_query_stream_sse(
            self,
            question,
            system_prompt=system_prompt,
            api_key=api_key,
            model=model,
            max_steps=max_steps,
            output_format=output_format,
        )
    
    def _execute_query_stream_workflow(
        self,
        question: str,
        output_format: str = "sse"
    ) -> Generator[str, None, None]:
        """
        使用工作流模式执行查询（新方法）
        
        设计：
        - 与现有 execute_query_stream 并行存在
        - 可通过配置开关选择使用哪种模式
        - 支持 text 和 sse 两种输出格式
        
        Args:
            question: 用户问题
            output_format: 输出格式 ("text" 或 "sse")
        
        Yields:
            格式化的事件字符串
        """
        try:
            from app.core.workflow.executor import WorkflowExecutor
            from app.core.holmes.streaming import create_sse_message_cn, format_duration
            
            # 创建执行器
            executor = WorkflowExecutor(holmes_service=self)
            
            # text 格式输出（终端友好）
            if output_format == "text":
                yield from self._workflow_to_text(executor, question)
                return
            
            # SSE 格式输出
            for event in executor.execute_stream(question):
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
        question: str
    ) -> Generator[str, None, None]:
        """
        工作流执行结果转换为美观的文本格式
        专为终端 curl 等命令行工具优化
        """
        from app.core.holmes.streaming import format_duration
        import json

        def emit(text: str) -> str:
            return text + "\n"

        # 节点输出格式化函数（局部函数，不需要 self）
        def format_layer_node_output(snapshot: dict) -> str:
            """格式化问题定位节点的输出"""
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
            """格式化证据采集节点的输出"""
            lines = []
            count = snapshot.get("evidence_count", 0)
            collected = snapshot.get("collected_count", 0)
            completeness = snapshot.get("completeness", 0) or 0

            lines.append(f"**证据数量**: {count}")
            lines.append(f"**已采集**: {collected}")
            lines.append(f"**完整度**: {completeness:.0%}")

            return "\n".join(lines)

        def format_rca_node_output(snapshot: dict) -> str:
            """格式化根因分析节点的输出"""
            lines = []
            root_cause = snapshot.get("root_cause", "")
            conf = snapshot.get("confidence")
            conf_str = f"{conf:.0%}" if conf else "?"

            lines.append(f"**根因**: {root_cause}")
            lines.append(f"**置信度**: {conf_str}")

            return "\n".join(lines)

        yield emit("=" * 70)
        yield emit("🔄 K8s AIOps Copilot - 工作流诊断模式")
        yield emit("=" * 70)
        yield emit("")

        # 安全截断问题文本（避免在多字节字符中间截断）
        question_display = question[:100] if len(question) > 100 else question
        yield emit(f"📝 问题: {question_display}")
        yield emit("")
        yield emit("-" * 70)

        final_answer = ""
        metrics_data = None
        # 用于收集各节点的详细输出
        node_outputs = {
            "layer": "",
            "evidence": "",
            "rca": "",
            "conclusion": ""
        }

        for event in executor.execute_stream(question):
            event_type = event.get("type", "unknown")
            
            if event_type == "run_start":
                run_id = event.get("run_id", "?")
                yield emit(f"🚀 开始诊断 [run_id: {run_id}]")
                yield emit("")
            
            elif event_type == "node_start":
                node_name = event.get("node_name", event.get("node", "?"))
                yield emit(f"📍 [{node_name}] 执行中...")
            
            elif event_type == "node_complete":
                node_name = event.get("node_name", event.get("node", "?"))
                duration = event.get("duration_seconds", 0)
                snapshot = event.get("state_snapshot", {})

                yield emit(f"   ✅ [{node_name}] 完成 ({format_duration(duration)})")
                yield emit("")

                # 输出节点详细内容
                node_id = event.get("node", "")
                if node_id == "layer":
                    yield emit("   ┌──────────────────────────────────────────┐")
                    yield emit("   │ 📊 问题定位结果                              │")
                    yield emit("   └──────────────────────────────────────────┘")
                    yield emit("")
                    layer = snapshot.get("layer", "?")
                    conf = snapshot.get("layer_confidence", 0) or 0
                    yield emit(f"   层级: {layer}")
                    yield emit(f"   置信度: {conf:.0%}")
                    # 保存节点分析用于最终答案（不在节点完成时显示完整分析）
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
                    # 保存节点分析用于最终答案（不在节点完成时显示完整分析）
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
                        yield emit(f"   根因: {root_cause}")
                    yield emit(f"   置信度: {conf_str}")

                    # 显示因果链
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

                    # 保存节点分析用于最终答案（不在节点完成时显示完整分析）
                    node_outputs["rca"] = snapshot.get("rca_analysis", "") or format_rca_node_output(snapshot)

                elif node_id == "conclusion":
                    yield emit("   ┌──────────────────────────────────────────┐")
                    yield emit("   │ 📋 汇总总结结果                              │")
                    yield emit("   └──────────────────────────────────────────┘")
                    yield emit("")
                    length = snapshot.get("conclusion_length", 0)
                    yield emit(f"   报告长度: {length} 字符")
                    # 节点输出将在 final 事件中保存

                yield emit("")
            
            elif event_type == "final":
                final_answer = event.get("answer", "")
                metrics_data = event.get("metrics", {})
                elapsed = event.get("elapsed_seconds", 0)
                # 保存结论节点输出
                node_outputs["conclusion"] = final_answer or "（汇总节点生成最终报告）"
                yield emit("-" * 70)
                yield emit(f"📊 诊断完成! 总耗时: {format_duration(elapsed)}")
                yield emit("-" * 70)
                yield emit("")
            
            elif event_type == "error":
                error = event.get("error", "未知错误")
                yield emit(f"❌ 错误: {error}")
                yield emit("")
        
        # 输出最终报告（只输出节点4的完整 Markdown 报告）
        if final_answer:
            yield emit("=" * 70)
            yield emit("🎯 诊断报告")
            yield emit("=" * 70)
            yield emit("")

            # 只输出节点4（汇总总结）的完整 Markdown 报告
            if node_outputs["conclusion"]:
                yield emit("## 📋 节点四：汇总总结")
                yield emit("-" * 70)
                yield emit(node_outputs["conclusion"])
                yield emit("")
        
        # 输出指标摘要
        if metrics_data:
            yield emit("-" * 70)
            yield emit("📈 质量指标")
            yield emit("-" * 70)

            mttr = metrics_data.get("mttr", {})
            evidence = metrics_data.get("evidence_completeness", {})
            rca = metrics_data.get("root_cause_confidence", {})

            mttr_pass = "✅" if mttr.get("pass") else "❌"
            evidence_pass = "✅" if evidence.get("pass") else "⚠️"
            rca_pass = "✅" if rca.get("pass") else "⚠️"

            yield emit(f"  MTTR:        {mttr.get('value', '?')} {mttr_pass} (要求 < 10m)")
            yield emit(f"  根因置信度: {rca.get('value', '?')} {rca_pass} (要求 >= 80%)")
            yield emit(f"  证据完整率: {evidence.get('value', '?')} {evidence_pass} (要求 > 90%)")
            yield emit("")

        yield emit("=" * 70)
        yield emit("✅ 诊断完成!")
        yield emit("=" * 70)
    
    def _execute_query_stream_text(
        self,
        question: str,
        system_prompt: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_steps: int = 50
    ) -> Generator[str, None, None]:
        """
        执行查询并以易读的纯文本格式流式返回结果
        专为 curl 等命令行工具优化
        """
        yield from execute_query_stream_text(self, question, system_prompt, api_key, model, max_steps)
    
    def get_tools_info(self) -> dict:
        """获取可用工具信息"""
        self.initialize()
        
        tools = list(self.ai.tool_executor.tools_by_name.keys())
        toolsets = [{
            "name": toolset.name,
            "enabled": toolset.enabled,
            "status": toolset.status.value if hasattr(toolset.status, 'value') else str(toolset.status)
        } for toolset in self.ai.tool_executor.toolsets]
        
        return {
            "success": True,
            "total_tools": len(tools),
            "tools": sorted(tools),
            "toolsets": toolsets
        }

    def get_tools_detail(self) -> dict:
        """
        获取更详细的工具信息（面向排障/二次开发）

        目标：
        - 看清楚每个 toolset 下有哪些 tools（例如 bash/kubernetes/helm）
        - 尽量输出每个 tool 的描述与参数结构（不同版本 holmesgpt/工具对象字段可能不同，因此做兼容探测）
        """
        self.initialize()

        tool_executor = self.ai.tool_executor
        tools_by_name = tool_executor.tools_by_name

        def _tool_to_dict(tool_obj: Any) -> Dict[str, Any]:
            # 兼容不同 tool 实现
            d: Dict[str, Any] = {"name": getattr(tool_obj, "name", None) or str(tool_obj)}
            for attr in ("description", "doc", "help", "llm_instructions"):
                v = getattr(tool_obj, attr, None)
                if isinstance(v, str) and v.strip():
                    d["description"] = v.strip()
                    break

            # 参数 schema：常见字段尝试
            schema = None
            for attr in ("args_schema", "parameters", "input_schema", "schema"):
                v = getattr(tool_obj, attr, None)
                if v is None:
                    continue
                # pydantic model / dict / callable
                try:
                    if hasattr(v, "model_json_schema"):
                        schema = v.model_json_schema()
                    elif isinstance(v, dict):
                        schema = v
                    elif hasattr(v, "schema"):
                        schema = v.schema()
                except Exception:
                    schema = None
                if schema:
                    break
            if schema:
                d["schema"] = schema
            return d
            # 注释掉 schema 输出（避免终端 JSON 解析错误）
            # d["schema"] = schema  # 暂时禁用，避免终端误解析

        toolsets_detail = []
        for toolset in tool_executor.toolsets:
            ts_tools = []
            if hasattr(toolset, "tools") and toolset.tools:
                for t in toolset.tools:
                    name = getattr(t, "name", None)
                    if name and name in tools_by_name:
                        ts_tools.append(_tool_to_dict(tools_by_name[name]))

            toolsets_detail.append(
                {
                    "name": getattr(toolset, "name", str(toolset)),
                    "type": toolset.__class__.__name__,
                    "enabled": bool(getattr(toolset, "enabled", False)),
                    "status": getattr(getattr(toolset, "status", None), "value", None)
                    or str(getattr(toolset, "status", "")),
                    "error": str(getattr(toolset, "error", ""))[:500] if getattr(toolset, "error", None) else None,
                    "tools_count": len(ts_tools),
                    "tools": ts_tools,
                }
            )

        return {
            "success": True,
            "total_registered_tools": len(tools_by_name),
            "toolsets": toolsets_detail,
        }
    
    def health_check(self) -> dict:
        """健康检查"""
        if self.config is not None and self.ai is not None:
            return {
                "status": "healthy",
                "config_loaded": True,
                "ai_initialized": True
            }

        if self._init_in_progress:
            return {
                "status": "initializing",
                "config_loaded": self.config is not None,
                "ai_initialized": self.ai is not None,
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
            "ai_initialized": self.ai is not None
        }


# 全局服务实例（单例模式）
_global_service: Optional[HolmesService] = None


def get_service() -> HolmesService:
    """获取全局服务实例"""
    global _global_service
    if _global_service is None:
        _global_service = HolmesService()
    return _global_service

