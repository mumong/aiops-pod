"""
工作流报告器

职责：
- 诊断报告保存
- 从工作流状态提取质量指标
- Runbook 识别
- 置信度计算
"""

import json as _json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from app.core.workflow.metrics import WorkflowMetrics
from app.core.workflow.state import WorkflowState

logger = logging.getLogger(__name__)


def _normalize_runbook_text(text: str) -> str:
    if not text:
        return ""
    normalized = text.strip().lower()
    normalized = re.sub(r"\.md$", "", normalized)
    normalized = re.sub(r"^[#\s]+", "", normalized)
    normalized = re.sub(r"[`*_\-\(\)\[\]{}:：,，。.!！？/\\|【】<>\"'“”‘’]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _extract_catalog_title(description: str) -> str:
    if not description:
        return ""
    title = re.sub(r"^【[^】]+】", "", description).strip()
    if "—" in title:
        title = title.split("—", 1)[0].strip()
    return title


def _build_runbook_lookup(runbook_catalog: Any) -> Dict[str, str]:
    lookup: Dict[str, str] = {}
    if not runbook_catalog or not hasattr(runbook_catalog, "catalog"):
        return lookup

    for entry in getattr(runbook_catalog, "catalog", []) or []:
        canonical_id = (getattr(entry, "id", "") or "").strip()
        if not canonical_id:
            continue

        candidates = [
            canonical_id,
            getattr(entry, "link", "") or "",
            getattr(entry, "description", "") or "",
            _extract_catalog_title(getattr(entry, "description", "") or ""),
        ]
        for candidate in candidates:
            key = _normalize_runbook_text(candidate)
            if key:
                lookup[key] = canonical_id

    return lookup


def _canonicalize_runbook_name(name: str, lookup: Dict[str, str]) -> Optional[str]:
    if not name:
        return None
    if not lookup:
        return name.strip() or None

    key = _normalize_runbook_text(name)
    if not key:
        return None

    if key in lookup:
        return lookup[key]

    for candidate_key, canonical_id in lookup.items():
        if key and (key in candidate_key or candidate_key in key):
            return canonical_id

    return None


def save_report(reports_dir: str, layer: Any, question: str, full_answer: str) -> None:
    """保存诊断报告到固定目录"""
    try:
        import re as _re

        rdir = Path(reports_dir)
        logger.info(f"📄 [报告保存] 目标目录: {rdir} (存在: {rdir.exists()})")

        rdir.mkdir(parents=True, exist_ok=True)

        # 从报告文本中提取实际层级（conclusion 节点的判断比 layer 节点更准确）
        layer_str = extract_layer_from_report(full_answer)
        if not layer_str:
            layer_str = layer.value if hasattr(layer, "value") else str(layer or "UNKNOWN")
        logger.info(f"📄 [报告保存] 层级: {layer_str}, 问题: {question[:50]}")

        # 从问题中提取摘要（去掉特殊字符，截取前30字符）
        summary = _re.sub(r'[\\/:*?"<>|\n\r\t]', '', question)[:30].strip()
        if not summary:
            summary = "query"

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{layer_str}-{summary}_{ts}.md"
        filepath = rdir / filename

        content_size = len(full_answer.encode("utf-8"))
        filepath.write_text(full_answer, encoding="utf-8")
        logger.info(f"📄 [报告保存] 成功: {filepath} ({content_size} bytes)")
    except PermissionError as e:
        logger.error(f"❌ [报告保存] 权限不足: {e} (目录: {reports_dir})")
    except OSError as e:
        logger.error(f"❌ [报告保存] 文件系统错误: {e} (目录: {reports_dir})")
    except Exception as e:
        logger.error(f"❌ [报告保存] 未知错误: {type(e).__name__}: {e}", exc_info=True)


def extract_layer_from_report(text: str) -> str:
    """从报告文本中提取实际层级（优先用 conclusion 的判断）"""
    # 方法1: 表格格式 "| **问题层级** | L0 - xxx |"
    m = re.search(r'\|\s*\*{0,2}问题层级\*{0,2}\s*\|\s*\*{0,2}\s*(L[0-4]|QUERY)', text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    # 方法2: "**层级**: L0" 或 "- **层级**: L0" 或 "层级: L0"
    m = re.search(r'\*{0,2}层级\*{0,2}[：:\s]*\*{0,2}\s*(L[0-4]|QUERY)', text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    return ""


def update_metrics_from_state(
    metrics: WorkflowMetrics,
    state: WorkflowState,
    runbook_catalog: Any = None,
    holmes_service: Any = None,
) -> None:
    """从最终状态更新指标

    Args:
        metrics: WorkflowMetrics 实例
        state: 工作流最终状态
        runbook_catalog: Runbook 目录（用于匹配）
        holmes_service: HolmesService 实例（用于获取 raw_config）
    """

    # 证据完整率
    evidence_items = state.get("evidence_items", [])
    metrics.evidence_planned = len(evidence_items)
    metrics.evidence_collected = sum(1 for e in evidence_items if getattr(e, 'collected', False))

    # 填充证据详情（每项证据的名称+级别+状态）
    metrics.evidence_details = []
    for e in evidence_items:
        metrics.evidence_details.append({
            "description": getattr(e, 'description', '未知'),
            "level": getattr(e, 'level', 'IMPORTANT').value if hasattr(getattr(e, 'level', None), 'value') else str(getattr(e, 'level', 'IMPORTANT')),
            "collected": getattr(e, 'collected', False),
        })

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

    # （QualityScorer 在 runbook 提取之后执行，见下方）

    # ================================================================
    # Runbook 提取（从所有文本内容中搜索，不再依赖 tool_call_details）
    # ================================================================
    runbook_lookup = _build_runbook_lookup(runbook_catalog)
    runbook_ids: Set[str] = set()
    runbook_names: List[str] = []

    # 构建文本搜索源
    conclusion = (state.get("conclusion_formatted") or state.get("conclusion") or "")
    rca_analysis_raw = state.get("rca_analysis") or ""
    evidence_analysis_raw = state.get("evidence_analysis") or ""
    all_text = f"{conclusion}\n{rca_analysis_raw}\n{evidence_analysis_raw}"

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

        # ============================================================
        # 核心 Runbook 识别
        # 只用 AI 明确声明的，不做关键词猜测
        # ============================================================
        primary_runbooks: List[str] = []

        # 方法1: 直接从 state 读取（RCA 节点 lite 模式输出的 primary_runbooks）
        state_primary = state.get("primary_runbook_id")
        if state_primary:
            for rb in state_primary.split(", "):
                canonical = _canonicalize_runbook_name(rb.strip(), runbook_lookup)
                if canonical and canonical not in primary_runbooks:
                    primary_runbooks.append(canonical)

        # 方法2: 从 rca_analysis JSON 提取 primary_runbooks 字段
        if not primary_runbooks and rca_analysis_raw:
            try:
                rca_data = _json.loads(rca_analysis_raw) if isinstance(rca_analysis_raw, str) else rca_analysis_raw
                if isinstance(rca_data, dict):
                    ai_primary = rca_data.get("primary_runbooks", [])
                    if isinstance(ai_primary, list):
                        for rb in ai_primary:
                            canonical = _canonicalize_runbook_name(rb.strip(), runbook_lookup) if isinstance(rb, str) else None
                            if canonical and canonical not in primary_runbooks:
                                primary_runbooks.append(canonical)
                    # 方法2b: JSON 解析失败时从 llm_raw_analysis 提取
                    if not primary_runbooks:
                        raw = rca_data.get("llm_raw_analysis", "")
                        if raw:
                            for m in re.finditer(r'found a runbook named \*\*(.+?)\*\*', raw):
                                name = m.group(1).strip()
                                canonical = _canonicalize_runbook_name(name, runbook_lookup)
                                if canonical and canonical not in primary_runbooks:
                                    primary_runbooks.append(canonical)
            except (ValueError, TypeError):
                pass

        canonical_refs: List[str] = []
        for rb in sorted(runbook_ids):
            canonical = _canonicalize_runbook_name(rb, runbook_lookup)
            if canonical and canonical not in canonical_refs:
                canonical_refs.append(canonical)
        for name in runbook_names:
            canonical = _canonicalize_runbook_name(name, runbook_lookup)
            if canonical and canonical not in canonical_refs:
                canonical_refs.append(canonical)

        # 方法3: 如果 AI 没给出合法核心 runbook，则在唯一合法参考 runbook 场景下回退为该 runbook
        if not primary_runbooks and len(canonical_refs) == 1:
            primary_runbooks.append(canonical_refs[0])

        metrics.primary_runbook = ', '.join(primary_runbooks) if primary_runbooks else None

        # 参考 Runbook：仅展示 catalog 中存在的 canonical runbook id
        all_ref_names = list(primary_runbooks)
        for ref in canonical_refs:
            if ref not in all_ref_names:
                all_ref_names.append(ref)

        # 过滤掉 QUERY 参考手册（非 QUERY 模式下不应出现）
        layer = state.get("layer")
        layer_val = layer.value if hasattr(layer, "value") else str(layer or "")
        if layer_val != "QUERY":
            all_ref_names = [n for n in all_ref_names if "QUERY" not in n.upper() and "快速查询参考" not in n]

        if all_ref_names:
            metrics.runbook_id = ', '.join(all_ref_names)
        else:
            metrics.runbook_id = None

        if metrics.primary_runbook:
            logger.info(f"   核心 Runbook: {metrics.primary_runbook}")
        logger.info(f"   参考 Runbook: {metrics.runbook_id}")
    else:
        metrics.runbook_matched = False
        metrics.runbook_id = None
        metrics.primary_runbook = None

    # ================================================================
    # Runbook 覆盖率（多维度加权评分）
    # 有 runbook 引用时保底 > 80%
    # ================================================================
    rb_dims = []
    # 维度1: Runbook 引用（权重 50%）— 是否调用了 runbook
    rb_ref_score = 1.0 if metrics.runbook_matched else 0.0
    rb_dims.append({
        "description": "Runbook 引用",
        "weight": 0.50, "score": rb_ref_score,
        "weighted_score": round(0.50 * rb_ref_score, 4),
    })

    # 维度2: 核心 Runbook 识别（权重 30%）— 是否识别出与诊断强相关的核心 runbook
    rb_primary_score = 1.0 if metrics.primary_runbook else (0.3 if metrics.runbook_matched else 0.0)
    rb_dims.append({
        "description": "核心 Runbook 识别",
        "weight": 0.30, "score": rb_primary_score,
        "weighted_score": round(0.30 * rb_primary_score, 4),
    })
    # 维度3: Runbook 结论关联（权重 20%）— 核心 runbook 是否在结论中被引用
    rb_conclusion_score = 0.0
    if metrics.primary_runbook and conclusion:
        # 检查 primary_runbook 的关键词是否出现在 conclusion 中
        primary_keywords = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', metrics.primary_runbook)
        matched_kw = sum(1 for kw in primary_keywords if kw.lower() in conclusion.lower())
        rb_conclusion_score = min(1.0, matched_kw / max(len(primary_keywords), 1))
    elif metrics.runbook_matched and conclusion:
        rb_conclusion_score = 0.3  # 有 runbook 但无 primary，给基础分
    rb_dims.append({
        "description": "Runbook 结论关联",
        "weight": 0.20, "score": rb_conclusion_score,
        "weighted_score": round(0.20 * rb_conclusion_score, 4),
    })

    rb_total = sum(d["weighted_score"] for d in rb_dims)
    # 保底：有 runbook 引用时至少 85%
    if metrics.runbook_matched:
        rb_total = max(0.85, rb_total)
    metrics.runbook_coverage_score = min(1.0, rb_total)
    metrics.runbook_coverage_breakdown = rb_dims
    logger.info(f"   Runbook 覆盖率: {metrics.runbook_coverage_score:.0%}")

    # ================================================================
    # 根因置信度 + 证据完整率（多维度加权评分）
    # 必须在 runbook 提取之后执行，确保 runbook_matched 已设置
    # ================================================================
    from app.core.workflow.quality_scorer import QualityScorer

    metrics_config = None
    if holmes_service:
        full_config = getattr(holmes_service, 'raw_config', None)
        if full_config and isinstance(full_config, dict):
            metrics_config = full_config.get("metrics")

    scorer = QualityScorer(metrics_config)

    # 计算根因置信度
    confidence_result = scorer.score_confidence(state, metrics)
    metrics.root_cause_confidence = confidence_result.final_score
    metrics.confidence_breakdown = [d.to_dict() for d in confidence_result.dimensions]
    metrics.confidence_penalties = [p.to_dict() for p in confidence_result.penalties]
    metrics.confidence_weighted_total = confidence_result.weighted_total
    metrics.confidence_fallback_applied = confidence_result.fallback_applied

    logger.info(
        f"   置信度评分: {confidence_result.final_score:.0%} "
        f"(加权 {confidence_result.weighted_total:.0%}, "
        f"fallback={confidence_result.fallback_applied})"
    )

    # 计算加权证据完整率
    ev_completeness, ev_detail = scorer.score_evidence_completeness(evidence_items)
    metrics.evidence_breakdown = ev_detail
