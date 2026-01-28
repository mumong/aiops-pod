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
from datetime import datetime
from typing import Generator, Dict, Any, Optional

from app.core.workflow.state import WorkflowState
from app.core.workflow.graph import build_diagnosis_workflow
from app.core.workflow.metrics import (
    WorkflowMetrics,
    start_workflow_metrics,
    finish_workflow_metrics,
    get_current_metrics,
)

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
        runbook_catalog = (
            holmes_service.merged_catalog
            if holmes_service and holmes_service.merged_catalog
            else None
        )
        self.workflow = build_diagnosis_workflow(holmes_service, metrics, runbook_catalog)
    
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

        total_start = time.time()
        
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
        
        # 执行工作流（流式）
        completed_nodes = set()  # 已完成的节点
        current_nodes = set()   # 当前批次的节点
        node_start_times = {}
        seq = 0
        final_state = initial_state.copy()

        try:
            for event in self.workflow.stream(initial_state):
                # LangGraph 返回格式: {node_name: updated_state}
                new_nodes_in_this_event = set()

                for node_name, updated_state in event.items():
                    new_nodes_in_this_event.add(node_name)

                    # 节点开始（只记录一次）
                    if node_name not in node_start_times:
                        node_start_times[node_name] = time.time()
                        metrics.start_node(node_name, self._get_node_display_name(node_name))

                        # 日志输出节点开始
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

                # 更新最终状态
                final_state.update(updated_state)

                # 检查是否有节点完成（不在当前事件中的节点）
                for node_name in current_nodes:
                    if node_name not in new_nodes_in_this_event:
                        # 节点完成
                        node_duration = time.time() - node_start_times.get(node_name, time.time())
                        metrics.finish_node(node_name, success=True)
                        completed_nodes.add(node_name)

                        # 提取节点输出摘要用于日志
                        snapshot = self._extract_state_snapshot(final_state, node_name)
                        node_summary = self._format_node_summary(node_name, final_state, snapshot)

                        # 日志输出节点完成和摘要
                        logger.info(f"✅ [{node_name}] 完成 ({node_duration:.1f}s)")
                        if node_summary:
                            logger.info(f"   {node_summary}")

                        yield {
                            "type": "node_complete",
                            "id": f"{run_id}-node_complete-{node_name}",
                            "run_id": run_id,
                            "seq": seq + 1,
                            "ts_ms": int(time.time() * 1000),
                            "node": node_name,
                            "node_name": self._get_node_display_name(node_name),
                            "duration_seconds": round(node_duration, 3),
                            "state_snapshot": snapshot,
                        }

                # 更新当前节点集合
                current_nodes = new_nodes_in_this_event
            
            # 更新指标
            self._update_metrics_from_state(metrics, final_state)
            
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
            logger.info(f"   MTTR: {metrics.mttr_formatted} {'✅' if metrics.mttr_pass else '❌'}")
            logger.info(f"   根因置信度: {metrics.root_cause_confidence:.0%} {'✅' if metrics.root_cause_accuracy_pass else '⚠️'}")
            logger.info(f"   证据完整率: {metrics.evidence_completeness:.0%} {'✅' if metrics.evidence_completeness_pass else '⚠️'}")
            
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
        # 证据完整率
        evidence_items = state.get("evidence_items", [])
        metrics.evidence_planned = len(evidence_items)
        metrics.evidence_collected = sum(1 for e in evidence_items if getattr(e, 'collected', False))
        
        # 根因置信度
        decision = state.get("deterministic_decision")
        if decision:
            metrics.root_cause_confidence = decision.confidence_score
        else:
            # 从 rca_analysis 中提取
            import json
            rca_analysis = state.get("rca_analysis", "{}")
            try:
                rca_data = json.loads(rca_analysis) if rca_analysis else {}
                metrics.root_cause_confidence = rca_data.get("confidence", 0.5)
            except:
                metrics.root_cause_confidence = 0.5
        
        # Runbook 使用记录（检查实际调用的 runbook）
        # 从工具调用结果中提取使用的 runbook ID
        runbook_ids_used = []
        runbook_names = []  # 存储中文runbook名称

        # 从 tool_call_details 中查找 runbook 相关调用
        for detail in metrics.tool_call_details:
            tool_name = detail.get('tool', '')
            result = detail.get('result', '')

            # 检查是否是 runbook 相关调用（扩展检测范围）
            # 支持多种工具名称：runbook, fetch_runbook, show_runbook等
            is_runbook_tool = (
                'runbook' in tool_name.lower() or
                'fetch' in tool_name.lower() or
                'show' in tool_name.lower()
            )

            if is_runbook_tool and result:
                # 提取 runbook 名称
                import re

                # 1. 尝试提取 Markdown 文件名
                runbook_match = re.search(r'[\w-]+\.md', result)
                if runbook_match:
                    runbook_id = runbook_match.group(0)
                    if runbook_id not in runbook_ids_used:
                        runbook_ids_used.append(runbook_id)

                # 2. 尝试提取中文 runbook 名称（如 "容器崩溃循环 (CrashLoopBackOff) 诊断手册"）
                chinese_runbook_match = re.search(r'[*【](.*?)[*】]', result)
                if chinese_runbook_match:
                    runbook_name = chinese_runbook_match.group(1).strip('*【】')
                    if runbook_name and runbook_name not in runbook_names:
                        runbook_names.append(runbook_name)

                # 3. 尝试提取以 ** 标记的 runbook 名称
                bold_runbook_match = re.search(r'\*\*(.+?)\*\*', result)
                if bold_runbook_match:
                    runbook_name = bold_runbook_match.group(1).strip()
                    if runbook_name and runbook_name not in runbook_names:
                        runbook_names.append(runbook_name)

        if runbook_ids_used or runbook_names:
            metrics.runbook_matched = True
            # 优先显示中文runbook名称，如果没有则显示文件ID
            metrics.runbook_id = ', '.join(runbook_names) if runbook_names else ', '.join(runbook_ids_used)
            logger.info(f"   Runbook 使用: {metrics.runbook_id}")
        else:
            metrics.runbook_matched = False
            metrics.runbook_id = None
