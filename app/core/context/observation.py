"""Bounded tool observation processing.

The processor archives full raw tool output, extracts compact structured facts
for known heavy K8s tools, and returns a summary small enough to feed back to the
main agent.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict, Optional

from .archive import ContextArchive, get_archive_root


Summarizer = Callable[[str, str, str], Optional[str]]


class ObservationProcessor:
    HEAVY_TOOLS = {
        "kubectl_get_by_kind_in_cluster",
        "kubectl_get_by_kind_in_namespace",
        "kubectl_get_yaml",
        "kubectl_describe",
        "kubectl_events",
        "kubernetes_jq_query",
        "kubernetes_tabular_query",
    }
    MEDIUM_TOOLS = {
        "kubectl_get_by_name",
        "kubectl_find_resource",
        "kubectl_lineage_children",
        "kubectl_lineage_parents",
        "execute_prometheus_instant_query",
        "get_prometheus_target",
    }

    def __init__(
        self,
        archive_root: Optional[str] = None,
        max_observation_chars: int = 3000,
        summarizer: Optional[Summarizer] = None,
        summary_mode: str = "rule",
    ):
        self.archive_root = archive_root or get_archive_root()
        self.max_observation_chars = max_observation_chars
        self.summarizer = summarizer
        normalized = (summary_mode or "rule").strip().lower()
        self.summary_mode = normalized if normalized in {"rule", "ai"} else "rule"

    def process(
        self,
        run_id: str,
        node_id: str,
        sequence: int,
        tool_name: str,
        raw_content: str,
    ) -> Dict[str, Any]:
        raw = raw_content or ""
        tool = tool_name or "unknown"
        structured: Dict[str, Any]
        summary: str
        processor = "passthrough"

        try:
            structured, summary, processor = self._extract(tool, raw)
        except Exception as exc:
            structured = {"status": "extract_failed", "error": str(exc)}
            summary = self._generic_summary(tool, raw)
            processor = "generic"

        should_llm_summarize = self.summary_mode == "ai" or len(summary) > self.max_observation_chars
        if should_llm_summarize and self.summarizer:
            llm_summary = self.summarizer(tool, raw, summary)
            if llm_summary:
                summary = llm_summary
                processor = f"{processor}+llm"

        summary = self._bound_summary(summary, raw)

        refs = ContextArchive(run_id=run_id, root=self.archive_root).write_tool_artifact(
            node_id=node_id,
            sequence=sequence,
            tool_name=tool,
            raw=raw,
            structured=structured,
            summary=summary,
        )
        return {
            "tool": tool,
            "status": "success",
            "summary": summary,
            "structured": structured,
            "raw_chars": len(raw),
            "summary_chars": len(summary),
            "processed": True,
            "processor": processor,
            **refs,
        }

    def _extract(self, tool: str, raw: str) -> tuple[Dict[str, Any], str, str]:
        if tool == "kubectl_events":
            return self._extract_events(raw)
        if tool == "kubectl_describe":
            return self._extract_describe(raw)
        if tool in {"kubectl_get_by_kind_in_cluster", "kubectl_get_by_kind_in_namespace", "kubernetes_tabular_query"}:
            return self._extract_table(tool, raw)
        if tool == "kubernetes_jq_query":
            return self._extract_jq(raw)
        if tool == "kubectl_get_yaml":
            return self._extract_yaml(raw)

        if tool in self.MEDIUM_TOOLS and len(raw) <= self.max_observation_chars:
            return {"status": "kept_small_output"}, raw, "passthrough"
        return {"status": "generic_summary"}, self._generic_summary(tool, raw), "generic"

    def _extract_events(self, raw: str) -> tuple[Dict[str, Any], str, str]:
        if re.search(r"no events found|no resources found", raw, re.IGNORECASE):
            structured = {"status": "no_events_found", "warnings": []}
            return structured, "工具成功执行，但没有找到事件；这是空/负向观察，不能当作异常已被验证。", "k8s_events"

        lines = [ln for ln in raw.splitlines() if ln.strip()]
        warning_lines = [ln for ln in lines if re.search(r"\bWarning\b|Failed|BackOff|x509|ErrImagePull|ImagePullBackOff", ln)]
        selected = warning_lines[:20] or lines[:20]
        structured = {
            "status": "events_found",
            "warning_count": len(warning_lines),
            "selected_events": selected,
        }
        summary = "kubectl_events 摘要:\n" + "\n".join(selected)
        return structured, summary, "k8s_events"

    def _extract_describe(self, raw: str) -> tuple[Dict[str, Any], str, str]:
        fields = {}
        for key in ["Name", "Namespace", "Node", "Status", "Reason", "Message"]:
            match = re.search(rf"^{re.escape(key)}:\s*(.+)$", raw, re.MULTILINE)
            if match:
                fields[key.lower()] = match.group(1).strip()

        interesting = []
        for line in raw.splitlines():
            if re.search(
                r"State:|Last State:|Reason:|Exit Code:|Warning|Failed|BackOff|"
                r"ImagePullBackOff|ErrImagePull|CrashLoopBackOff|OOMKilled|"
                r"FailedScheduling|MountVolume|x509|NotReady",
                line,
            ):
                interesting.append(line.rstrip())

        structured = {
            **fields,
            "signals": interesting[:80],
        }
        summary_lines = [
            "kubectl_describe 摘要:",
            *[f"{k}: {v}" for k, v in fields.items()],
        ]
        if interesting:
            summary_lines.append("关键状态/事件:")
            summary_lines.extend(interesting[:40])
        return structured, "\n".join(summary_lines), "k8s_describe"

    def _extract_table(self, tool: str, raw: str) -> tuple[Dict[str, Any], str, str]:
        lines = [ln for ln in raw.splitlines() if ln.strip()]
        if not lines:
            return {"status": "empty"}, "工具返回为空；不能作为正向健康证据。", "k8s_table"
        if re.search(r"command failed|error from server|notfound|not found", raw, re.IGNORECASE):
            return {"status": "command_failed", "raw_preview": raw[:1000]}, self._generic_summary(tool, raw), "k8s_table"

        header = lines[0]
        abnormal = [
            ln for ln in lines[1:]
            if re.search(
                r"CrashLoopBackOff|ImagePullBackOff|ErrImagePull|OOMKilled|Evicted|"
                r"Pending|Failed|Error|NotReady|Unknown|0/\d+|<none>\s*$",
                ln,
                re.IGNORECASE,
            )
        ]
        status_counts: Dict[str, int] = {}
        for ln in lines[1:]:
            for status in re.findall(r"\b(Running|Pending|Failed|Succeeded|CrashLoopBackOff|ImagePullBackOff|ErrImagePull|OOMKilled|Evicted|NotReady|Ready)\b", ln):
                status_counts[status] = status_counts.get(status, 0) + 1

        selected = abnormal[:50] if abnormal else lines[1:21]
        structured = {
            "status": "table_summarized",
            "row_count": max(0, len(lines) - 1),
            "abnormal_count": len(abnormal),
            "status_counts": status_counts,
            "header": header,
            "selected_rows": selected,
        }
        label = "异常行" if abnormal else "样例行"
        summary = f"{tool} 表格摘要: rows={structured['row_count']} abnormal={len(abnormal)} status_counts={status_counts}\n{header}\n# {label}\n" + "\n".join(selected)
        return structured, summary, "k8s_table"

    def _extract_jq(self, raw: str) -> tuple[Dict[str, Any], str, str]:
        stripped = raw.strip()
        try:
            parsed = json.loads(stripped)
            structured = {
                "status": "json_summarized",
                "type": type(parsed).__name__,
                "count": len(parsed) if isinstance(parsed, (list, dict)) else 1,
            }
            summary = json.dumps(parsed, ensure_ascii=False)[: self.max_observation_chars]
            return structured, summary, "k8s_jq"
        except Exception:
            return {"status": "text_summarized"}, self._generic_summary("kubernetes_jq_query", raw), "k8s_jq"

    def _extract_yaml(self, raw: str) -> tuple[Dict[str, Any], str, str]:
        # Keep this dependency-free; extract high-value YAML lines without full parsing.
        keep = []
        for line in raw.splitlines():
            if re.search(
                r"^kind:|^\s*name:|^\s*namespace:|^\s*image:|^\s*resources:|"
                r"^\s*limits:|^\s*requests:|^\s*env:|^\s*envFrom:|"
                r"^\s*volumes:|^\s*volumeMounts:|^\s*phase:|^\s*reason:|"
                r"^\s*message:|^\s*containerStatuses:",
                line,
            ):
                keep.append(line.rstrip())
        structured = {"status": "yaml_summarized", "selected_line_count": len(keep)}
        return structured, "kubectl_get_yaml 关键字段摘要:\n" + "\n".join(keep[:120]), "k8s_yaml"

    def _generic_summary(self, tool: str, raw: str) -> str:
        lines = [ln for ln in raw.splitlines() if ln.strip()]
        head = "\n".join(lines[:40])
        return f"{tool} 输出摘要: raw_chars={len(raw)} lines={len(lines)}\n{head}"

    def _bound_summary(self, summary: str, raw: str) -> str:
        if len(summary) <= self.max_observation_chars:
            return summary
        suffix = f"\n... (已压缩/截断，原始 {len(raw)} 字符，完整内容见 raw_ref)"
        limit = max(0, self.max_observation_chars - len(suffix))
        return summary[:limit] + suffix
