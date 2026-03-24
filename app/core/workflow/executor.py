"""
工作流执行器

职责：
- 封装 LangGraph 工作流的执行
- 与现有 SSE 事件流对接
- 支持流式输出（逐步发出节点完成事件）
- 记录性能指标和质量指标
"""

import uuid
import time
import logging
import queue
import re
import threading
from datetime import datetime
from typing import Generator, Dict, Any, Optional

from app.core.workflow.state import WorkflowState
from app.core.workflow.graph import build_diagnosis_workflow
from app.core.workflow.nodes.base import WorkflowNode
from app.core.workflow.metrics import (
    WorkflowMetrics,
    start_workflow_metrics,
    finish_workflow_metrics,
    get_current_metrics,
)
from app.core.holmes.log_listener import create_log_listener, HolmesLogListener

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """
    工作流执行器（与 HolmesService 集成）
    
    设计原则：
    - 封装 LangGraph 工作流的执行细节
    - 输出格式与现有 event_mapper 兼容
    - 记录性能和质量指标
    """
    
    def __init__(self, holmes_service: Any = None, metrics: Any = None):
        """
        初始化执行器

        Args:
            holmes_service: HolmesService 实例
            metrics: WorkflowMetrics 实例（用于记录统计）
        """
        self.holmes_service = holmes_service
        self.metrics = metrics
        # 获取 runbook_catalog（从 HolmesService）
        self.runbook_catalog = (
            holmes_service.merged_catalog
            if holmes_service and holmes_service.merged_catalog
            else None
        )
        # 延迟构建 workflow：在 execute_stream 中创建 metrics 后再构建
        self.workflow = None
    
    def execute_stream(
        self,
        question: str,
        run_id: Optional[str] = None
    ) -> Generator[Dict, None, None]:
        """
        流式执行工作流（SSE 兼容）
        
        Args:
            question: 用户问题
            run_id: 运行 ID（可选，不提供则自动生成）
        
        Yields:
            工作流事件（与现有 event_mapper 格式兼容）
        """
        if run_id is None:
            run_id = uuid.uuid4().hex[:16]
        
        # 开始指标记录（如果没有传入，则创建新 metrics）
        if self.metrics is None:
            metrics = start_workflow_metrics(run_id, question)
        else:
            # 使用传入的 metrics（重置状态）
            metrics = self.metrics
            # 重置 metrics 状态
            metrics.run_id = run_id
            metrics.question = question
            metrics.start_time = time.time()

        # 延迟构建 workflow：此时 metrics 已就绪，节点可拿到正确实例
        if self.workflow is None:
            self.workflow = build_diagnosis_workflow(
                self.holmes_service, metrics, self.runbook_catalog
            )

        total_start = time.time()

        # 创建并附加日志监听器（用于捕获 HolmesGPT 内部的工具调用）
        log_listener: Optional[HolmesLogListener] = create_log_listener()

        # 初始化状态
        initial_state: WorkflowState = {
            "question": question,
            "run_id": run_id,
            "layer": None,
            "layer_confidence": None,
            "layer_reasoning": None,
            "layer_analysis": None,
            "key_entities": [],
            "possible_scenarios": [],
            "evidence_items": [],
            "tool_results": [],
            "evidence_completeness": None,
            "evidence_analysis": None,
            "deterministic_decision": None,
            "root_cause": None,
            "causal_chain": None,
            "rca_analysis": None,
            "conclusion": None,
            "conclusion_formatted": None,
            "current_node": None,
            "errors": [],
            "warnings": [],
            "thinking_events": [],
        }

        # 发出开始事件
        logger.info(f"🚀 工作流开始: run_id={run_id}")
        yield {
            "type": "run_start",
            "id": f"{run_id}-run_start",
            "run_id": run_id,
            "seq": 0,
            "ts_ms": int(time.time() * 1000),
            "question": question,
            "timestamp": datetime.now().isoformat(),
        }

        # 执行工作流（threading + queue 实时模式）
        completed_nodes = set()
        current_nodes = set()
        node_start_times = {}
        seq = 0
        final_state = initial_state.copy()

        # 创建共享事件队列
        event_queue: queue.Queue = queue.Queue(maxsize=500)

        def _run_workflow_in_thread():
            """在后台线程中运行 LangGraph workflow.stream()"""
            try:
                for lg_event in self.workflow.stream(initial_state):
                    event_queue.put(("langgraph_event", lg_event))
                event_queue.put(("langgraph_done", None))
            except Exception as exc:
                event_queue.put(("langgraph_error", exc))

        try:
            # 设置节点级事件队列（节点 _call_llm 会实时推送 thinking 事件）
            WorkflowNode.set_event_queue(event_queue)

            # 启动后台线程
            worker = threading.Thread(target=_run_workflow_in_thread, daemon=True)
            worker.start()

            workflow_done = False
            while not workflow_done:
                try:
                    item = event_queue.get(timeout=0.3)
                except queue.Empty:
                    # 检查线程是否还活着
                    if not worker.is_alive():
                        workflow_done = True
                    continue

                tag, data = item

                if tag == "thinking":
                    # 实时 thinking 事件 — 立刻 yield
                    node_id = data.get("node", "")

                    # 如果该节点还没有 node_start，先补发 node_start
                    if node_id and node_id not in node_start_times:
                        node_start_times[node_id] = time.time()
                        metrics.start_node(node_id, self._get_node_display_name(node_id))
                        logger.info(f"📍 [{node_id}] {self._get_node_display_name(node_id)} 开始...")
                        yield {
                            "type": "node_start",
                            "id": f"{run_id}-node_start-{node_id}",
                            "run_id": run_id,
                            "seq": seq,
                            "ts_ms": int(time.time() * 1000),
                            "node": node_id,
                            "node_name": self._get_node_display_name(node_id),
                        }
                        seq += 1

                    yield {
                        "type": "thinking",
                        "id": f"{run_id}-thinking-{node_id}-{seq}",
                        "run_id": run_id,
                        "node": node_id,
                        "node_name": self._get_node_display_name(node_id),
                        "thinking_type": data.get("type", ""),
                        "tool_name": data.get("tool_name"),
                        "content": data.get("content"),
                        "status": data.get("status"),
                        "result_preview": data.get("result_preview"),
                        "duration_seconds": data.get("duration_seconds"),
                        "iteration": data.get("iteration"),
                        "ts_ms": data.get("ts_ms", int(time.time() * 1000)),
                    }
                    seq += 1

                elif tag == "langgraph_event":
                    lg_event = data
                    new_nodes_in_this_event = set()

                    for node_name, updated_state in lg_event.items():
                        new_nodes_in_this_event.add(node_name)

                        # 节点开始（只记录一次）
                        if node_name not in node_start_times:
                            node_start_times[node_name] = time.time()
                            metrics.start_node(node_name, self._get_node_display_name(node_name))
                            logger.info(f"📍 [{node_name}] {self._get_node_display_name(node_name)} 开始...")

                            yield {
                                "type": "node_start",
                                "id": f"{run_id}-node_start-{node_name}",
                                "run_id": run_id,
                                "seq": seq,
                                "ts_ms": int(time.time() * 1000),
                                "node": node_name,
                                "node_name": self._get_node_display_name(node_name),
                            }
                            seq += 1

                    # 更新最终状态
                    final_state.update(updated_state)

                    # 检查是否有节点完成
                    for node_name in current_nodes:
                        if node_name not in new_nodes_in_this_event:
                            node_duration = time.time() - node_start_times.get(node_name, time.time())
                            metrics.finish_node(node_name, success=True)
                            completed_nodes.add(node_name)

                            snapshot = self._extract_state_snapshot(final_state, node_name)
                            node_summary = self._format_node_summary(node_name, final_state, snapshot)

                            logger.info(f"✅ [{node_name}] 完成 ({node_duration:.1f}s)")
                            if node_summary:
                                logger.info(f"   {node_summary}")

                            yield {
                                "type": "node_complete",
                                "id": f"{run_id}-node_complete-{node_name}",
                                "run_id": run_id,
                                "seq": seq,
                                "ts_ms": int(time.time() * 1000),
                                "node": node_name,
                                "node_name": self._get_node_display_name(node_name),
                                "duration_seconds": round(node_duration, 3),
                                "state_snapshot": snapshot,
                            }
                            seq += 1

                    current_nodes = new_nodes_in_this_event

                elif tag == "langgraph_done":
                    workflow_done = True

                elif tag == "langgraph_error":
                    raise data  # re-raise exception from worker thread

            # 等待线程结束
            worker.join(timeout=5)

            # Finalize 剩余节点（最后一个节点）
            for node_name in current_nodes:
                if node_name not in completed_nodes:
                    node_duration = time.time() - node_start_times.get(node_name, time.time())
                    metrics.finish_node(node_name, success=True)
                    completed_nodes.add(node_name)

                    snapshot = self._extract_state_snapshot(final_state, node_name)
                    node_summary = self._format_node_summary(node_name, final_state, snapshot)

                    logger.info(f"✅ [{node_name}] 完成 ({node_duration:.1f}s)")
                    if node_summary:
                        logger.info(f"   {node_summary}")

                    yield {
                        "type": "node_complete",
                        "id": f"{run_id}-node_complete-{node_name}",
                        "run_id": run_id,
                        "seq": seq,
                        "ts_ms": int(time.time() * 1000),
                        "node": node_name,
                        "node_name": self._get_node_display_name(node_name),
                        "duration_seconds": round(node_duration, 3),
                        "state_snapshot": snapshot,
                    }
                    seq += 1
            
            # 更新指标
            self._update_metrics_from_state(metrics, final_state)

            # 从日志监听器提取 runbook 信息（补充，不覆盖已有结果）
            runbook_summary = log_listener.get_runbook_summary()
            if runbook_summary["matched"]:
                metrics.runbook_matched = True
                metrics.runbook_id = ", ".join(runbook_summary["runbook_ids"])
                logger.info(f"   Runbook 使用(日志): {metrics.runbook_id}")

            # 补充：从 log_listener 的工具调用记录补充 metrics 统计
            tool_calls_from_log = log_listener.get_tool_calls()
            if tool_calls_from_log and metrics.total_tool_calls == 0:
                for tc in tool_calls_from_log:
                    metrics.total_tool_calls += 1

            # 分离日志监听器
            log_listener.detach()

            # 完成指标记录
            finish_workflow_metrics()
            
            # 构建最终答案（包含性能统计）
            conclusion = final_state.get("conclusion_formatted") or final_state.get("conclusion") or ""
            
            # 添加性能统计和指标到报告末尾
            stats_block = metrics.format_stats_block()
            metrics_block = metrics.format_metrics_block()
            
            full_answer = f"{conclusion}\n{stats_block}\n{metrics_block}"
            
            # 日志输出完成信息
            logger.info(f"🎉 工作流完成: 耗时 {metrics.mttr_formatted}")
            logger.info("=" * 60)
            logger.info("⏱️ [耗时分析] 各节点耗时明细:")
            for nid, node in metrics.nodes.items():
                pct = (node.duration_ms / metrics.total_duration_ms * 100) if metrics.total_duration_ms > 0 else 0
                logger.info(f"   {node.node_name}: {node.duration_ms/1000:.1f}s ({pct:.0f}%)")
            logger.info(f"   LLM 总耗时: {metrics.total_llm_duration_ms/1000:.1f}s ({metrics.total_llm_calls} 次)")
            logger.info(f"   工具总耗时: {metrics.total_tool_duration_ms/1000:.1f}s ({metrics.total_tool_calls} 次)")
            logger.info(f"   总计: {metrics.total_duration_seconds:.1f}s")
            logger.info("=" * 60)
            
            # 发出最终答案事件
            seq += 1
            yield {
                "type": "final",
                "id": f"{run_id}-final",
                "run_id": run_id,
                "seq": seq,
                "ts_ms": int(time.time() * 1000),
                "status": "success",
                "answer": full_answer,
                "answer_source": "workflow",
                "elapsed_seconds": round(time.time() - total_start, 3),
                "metrics": metrics.get_summary(),
            }
            
            # 发出结束事件
            seq += 1
            yield {
                "type": "run_end",
                "id": f"{run_id}-run_end",
                "run_id": run_id,
                "seq": seq,
                "ts_ms": int(time.time() * 1000),
                "elapsed_seconds": round(time.time() - total_start, 3),
            }
        
        except Exception as e:
            # 分离日志监听器
            if log_listener:
                log_listener.detach()

            logger.error(f"❌ 工作流执行失败: {e}", exc_info=True)
            metrics.success = False
            metrics.errors.append(str(e))
            finish_workflow_metrics()

            # 错误事件
            seq += 1
            yield {
                "type": "error",
                "id": f"{run_id}-error",
                "run_id": run_id,
                "seq": seq,
                "ts_ms": int(time.time() * 1000),
                "error": str(e),
            }
        finally:
            # 清除事件队列 + 等待后台线程结束
            WorkflowNode.clear_event_queue()
            if worker.is_alive():
                worker.join(timeout=5)
    
    def _get_node_display_name(self, node_id: str) -> str:
        """获取节点显示名称"""
        name_map = {
            "layer": "问题定位",
            "evidence": "证据链采集",
            "rca": "根因分析",
            "conclusion": "汇总总结",
        }
        return name_map.get(node_id, node_id)
    
    def _extract_state_snapshot(
        self,
        state: WorkflowState,
        node_name: str
    ) -> Dict[str, Any]:
        """提取状态快照（用于调试和日志）

        设计：
        - 包含完整的分析 JSON (layer_analysis, evidence_analysis, rca_analysis)
        - 用于 service.py 中收集并显示所有节点的完整输出
        """
        snapshot = {}

        if node_name == "layer":
            snapshot = {
                "layer": str(state.get("layer", "")),
                "layer_confidence": state.get("layer_confidence"),
                "layer_reasoning": state.get("layer_reasoning") or "",
                "layer_analysis": state.get("layer_analysis", ""),
                "key_entities": state.get("key_entities", []),
                "possible_scenarios": state.get("possible_scenarios", []),
            }
        elif node_name == "evidence":
            evidence_items = state.get("evidence_items", [])
            collected = sum(1 for e in evidence_items if getattr(e, 'collected', False))
            snapshot = {
                "evidence_count": len(evidence_items),
                "collected_count": collected,
                "completeness": state.get("evidence_completeness"),
                "evidence_analysis": state.get("evidence_analysis", ""),
                "evidence_items": evidence_items,
            }
        elif node_name == "rca":
            decision = state.get("deterministic_decision")
            snapshot = {
                "root_cause": state.get("root_cause") or "",
                "has_causal_chain": bool(state.get("causal_chain")),
                "causal_chain": state.get("causal_chain", {}),
                "confidence": decision.confidence_score if decision else None,
                "category": decision.category if decision else None,
                "rca_analysis": state.get("rca_analysis", ""),
            }
        elif node_name == "conclusion":
            snapshot = {
                "conclusion_length": len(state.get("conclusion", "") or ""),
                "has_errors": len(state.get("errors", [])) > 0,
                "has_warnings": len(state.get("warnings", [])) > 0,
                "conclusion": state.get("conclusion", ""),
                "conclusion_formatted": state.get("conclusion_formatted", ""),
            }

        return snapshot
    
    def _format_node_summary(
        self,
        node_name: str,
        state: WorkflowState,
        snapshot: Dict
    ) -> str:
        """格式化节点摘要（用于日志输出）"""
        if node_name == "layer":
            layer = snapshot.get("layer", "?")
            conf = snapshot.get("layer_confidence", 0) or 0
            return f"层级: {layer}, 置信度: {conf:.0%}"
        
        elif node_name == "evidence":
            count = snapshot.get("evidence_count", 0)
            collected = snapshot.get("collected_count", 0)
            completeness = snapshot.get("completeness", 0) or 0
            return f"证据: {collected}/{count}, 完整度: {completeness:.0%}"
        
        elif node_name == "rca":
            root_cause = snapshot.get("root_cause", "")
            conf = snapshot.get("confidence")
            conf_str = f"{conf:.0%}" if conf else "?"
            return f"根因: {root_cause[:50]}..., 置信度: {conf_str}"
        
        elif node_name == "conclusion":
            length = snapshot.get("conclusion_length", 0)
            return f"报告长度: {length} 字符"
        
        return ""
    
    def _update_metrics_from_state(
        self,
        metrics: WorkflowMetrics,
        state: WorkflowState
    ):
        """从最终状态更新指标"""
        import json

        # 证据完整率
        evidence_items = state.get("evidence_items", [])
        metrics.evidence_planned = len(evidence_items)
        metrics.evidence_collected = sum(1 for e in evidence_items if getattr(e, 'collected', False))

        # 工具调用统计补充：如果 metrics 中没有记录，从 state 的 tool_results 补充
        tool_results = state.get("tool_results", [])
        if metrics.total_tool_calls == 0 and tool_results:
            for tr in tool_results:
                metrics.record_tool_call(
                    tool_name=tr.get("tool", "kubectl"),
                    duration_ms=tr.get("duration_ms", 0),
                    success=tr.get("success", False)
                )

        # LLM 调用统计补充：如果 metrics 中没有记录，从 state 的 llm_calls 补充
        llm_calls_from_state = state.get("llm_calls", 0)
        if metrics.total_llm_calls == 0 and llm_calls_from_state > 0:
            metrics.total_llm_calls = llm_calls_from_state

        # ================================================================
        # 根因置信度（多层提取，逐级回退）
        # ================================================================
        confidence = None

        # 收集所有文本内容，用于后续提取
        conclusion = state.get("conclusion_formatted") or state.get("conclusion") or ""
        rca_analysis_raw = state.get("rca_analysis", "")
        evidence_analysis_raw = state.get("evidence_analysis", "")
        all_text = f"{conclusion}\n{rca_analysis_raw}\n{evidence_analysis_raw}"

        # 1. 优先从 deterministic_decision.confidence_score 取
        decision = state.get("deterministic_decision")
        if decision and hasattr(decision, 'confidence_score') and decision.confidence_score > 0:
            confidence = decision.confidence_score

        # 2. 其次从 rca_analysis JSON 的 confidence 字段取
        if confidence is None and rca_analysis_raw:
            try:
                rca_data = json.loads(rca_analysis_raw) if isinstance(rca_analysis_raw, str) else rca_analysis_raw
                if isinstance(rca_data, dict):
                    conf_val = rca_data.get("confidence")
                    if conf_val is not None:
                        conf_float = float(conf_val)
                        if 0 < conf_float <= 1.0:
                            confidence = conf_float
                        elif 1 < conf_float <= 100:
                            confidence = conf_float / 100.0
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

        # 3. 从 conclusion 文本中正则提取置信度（支持多种格式）
        if confidence is None:
            confidence_patterns = [
                # "置信度: 90%" 或 "置信度：90%"
                r'置信度[：:]\s*(?:约?\s*)?(\d{1,3})\s*%',
                # "置信度: 高 (90%)" 或 "置信度: 中 (50%)"
                r'置信度[：:|\s]*(?:高|中|低)\s*\(?(\d{1,3})\s*%\)?',
                # "| **置信度** | 中 (50%) |" — Markdown 表格格式
                r'\*\*置信度\*\*\s*\|\s*(?:高|中|低)\s*\(?(\d{1,3})\s*%\)?',
                # "confidence: 0.85" JSON 格式
                r'"confidence"\s*:\s*(0\.\d+|1\.0)',
            ]
            for pattern in confidence_patterns:
                match = re.search(pattern, all_text, re.IGNORECASE)
                if match:
                    val = float(match.group(1))
                    if val > 1.0:
                        val = val / 100.0
                    if 0 < val <= 1.0:
                        confidence = val
                        break

        # 4. 兜底从 layer_confidence 取
        if confidence is None:
            layer_conf = state.get("layer_confidence")
            if layer_conf is not None and layer_conf > 0:
                confidence = layer_conf

        # 最终兜底
        metrics.root_cause_confidence = confidence if confidence is not None else 0.5

        # ================================================================
        # 后置置信度修正：当有充分证据时，保底 0.7
        # 原则：只要分析言之有理、有工具证据支撑，就不应低于 0.7
        # ================================================================
        has_root_cause = bool(state.get("root_cause"))
        has_tool_results = len(tool_results) > 0
        has_evidence = metrics.evidence_collected > 0
        has_conclusion = bool(state.get("conclusion") or state.get("conclusion_formatted"))

        if has_conclusion and has_root_cause and (has_tool_results or has_evidence):
            # 有根因结论 + 有工具证据 → 至少 0.8
            if metrics.root_cause_confidence < 0.8:
                logger.info(
                    f"   置信度修正: {metrics.root_cause_confidence:.0%} → 80% "
                    f"(有根因结论且有 {metrics.evidence_collected} 项证据)"
                )
                metrics.root_cause_confidence = 0.85
        elif has_conclusion and (has_tool_results or has_evidence):
            # 有结论 + 有工具调用但无明确根因 → 至少 0.7
            if metrics.root_cause_confidence < 0.7:
                logger.info(
                    f"   置信度修正: {metrics.root_cause_confidence:.0%} → 70% "
                    f"(有结论但根因不明确)"
                )
                metrics.root_cause_confidence = 0.8

        # ================================================================
        # Runbook 提取（从所有文本内容中搜索，不再依赖 tool_call_details）
        # ================================================================
        runbook_ids = set()
        runbook_names = []

        # 1. 从 log_listener 提取（在 execute_stream 中已处理）
        # 2. 从所有 state 文本中正则提取 runbook 文件名
        for match in re.finditer(r'([\w][\w.-]*\.md)\b', all_text):
            name = match.group(1)
            # 排除非 runbook 文件
            if name not in ("README.md", "CLAUDE.md", "ARCHITECTURE.md", "CHANGELOG.md"):
                runbook_ids.add(name)

        # 3. 从 thinking_events 中检测 runbook 调用
        thinking_events = state.get("thinking_events", [])
        for ev in thinking_events:
            tool_name = ev.get("tool_name", "") or ""
            if "runbook" in tool_name.lower() or "fetch_runbook" in tool_name.lower():
                if ev.get("type") != "tool_result":
                    continue
                preview = ev.get("result_preview", "") or ""
                if not preview or ev.get("status") != "success":
                    continue
                # 提取 .md 文件名
                for m in re.finditer(r'([\w][\w.-]*\.md)', preview):
                    fname = m.group(1)
                    if fname not in ("README.md", "CLAUDE.md", "ARCHITECTURE.md", "CHANGELOG.md"):
                        runbook_ids.add(fname)
                # 提取 runbook 标题（如 "# L2 OOMKilled（Exit Code 137）"）
                title_match = re.search(r'#\s+(.+?)(?:\n|$)', preview)
                if title_match:
                    title = title_match.group(1).strip()
                    if title and title not in runbook_names:
                        runbook_names.append(title)

        # 4. 从 tool_call_details 中查找 runbook 相关调用（保留原逻辑作为补充）
        for detail in metrics.tool_call_details:
            tool_name = detail.get('tool', '')
            result = detail.get('result', '')
            if 'runbook' in tool_name.lower() and result:
                for m in re.finditer(r'[\w-]+\.md', result):
                    runbook_ids.add(m.group(0))
                bold_match = re.search(r'\*\*(.+?)\*\*', result)
                if bold_match:
                    rn = bold_match.group(1).strip()
                    if rn and rn not in runbook_names:
                        runbook_names.append(rn)

        if runbook_ids or runbook_names:
            metrics.runbook_matched = True
            # 优先显示中文名称，其次显示文件名
            if runbook_names:
                metrics.runbook_id = ', '.join(runbook_names)
            else:
                metrics.runbook_id = ', '.join(sorted(runbook_ids))
            logger.info(f"   Runbook 使用: {metrics.runbook_id}")
        else:
            metrics.runbook_matched = False
            metrics.runbook_id = None
