"""Bounded tool observation processing.

The processor archives full raw tool output, extracts compact structured facts
for known heavy K8s tools, and returns a summary small enough to feed back to the
main agent.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict, Optional

import yaml

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
    LOG_TOOLS = {
        "kubectl_logs",
        "kubectl_previous_logs",
        "kubectl_logs_all_containers",
        "kubectl_previous_logs_all_containers",
        "kubectl_container_logs",
        "kubectl_container_previous_logs",
        "kubectl_logs_grep",
        "kubectl_logs_all_containers_grep",
    }
    FULL_PASSTHROUGH_TOOLS = {
        "kubectl_run_image",
        "run_bash_command",
        "fetch_runbook",
    }

    def __init__(
        self,
        archive_root: Optional[str] = None,
        max_observation_chars: int = 3000,
        summarizer: Optional[Summarizer] = None,
        summary_mode: str = "rule",
        context_pressure_threshold: float = 0.8,
    ):
        self.archive_root = archive_root or get_archive_root()
        self.max_observation_chars = max_observation_chars
        self.summarizer = summarizer
        normalized = (summary_mode or "rule").strip().lower()
        self.summary_mode = normalized if normalized in {"rule", "ai"} else "rule"
        self.context_pressure_threshold = float(context_pressure_threshold or 0.8)

    def process(
        self,
        run_id: str,
        node_id: str,
        sequence: int,
        tool_name: str,
        raw_content: str,
        context_usage_ratio: Optional[float] = None,
        tool_args: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        raw = raw_content or ""
        tool = tool_name or "unknown"
        structured: Dict[str, Any]
        summary: str
        processor = "passthrough"
        full_passthrough = tool in self.FULL_PASSTHROUGH_TOOLS

        if full_passthrough:
            structured, _, extracted_processor = self._extract(tool, raw)
            if tool == "fetch_runbook":
                self._attach_runbook_metadata(structured, tool_args or {})
            summary = raw
            processor = f"{extracted_processor}+passthrough_full"
        else:
            try:
                structured, summary, processor = self._extract(tool, raw)
                if tool == "fetch_runbook":
                    self._attach_runbook_metadata(structured, tool_args or {})
            except Exception as exc:
                structured = {"status": "extract_failed", "error": str(exc)}
                summary = self._generic_summary(tool, raw)
                processor = "generic"

        semantic_success = self._is_semantically_successful(structured, summary)

        over_context_threshold = (
            context_usage_ratio is not None
            and context_usage_ratio >= self.context_pressure_threshold
        )
        if full_passthrough:
            should_llm_summarize = over_context_threshold
        else:
            should_llm_summarize = (
                over_context_threshold
                or self.summary_mode == "ai"
                or len(summary) > self.max_observation_chars
            )
        if should_llm_summarize and self.summarizer:
            llm_summary = self.summarizer(tool, raw, summary)
            if llm_summary:
                summary = llm_summary
                processor = f"{processor}+llm_budget" if full_passthrough else f"{processor}+llm"

        if not full_passthrough or should_llm_summarize:
            before_len = len(summary)
            summary = self._bound_summary(summary, raw)
            if over_context_threshold and len(summary) < before_len and "+llm" not in processor:
                processor = f"{processor}+context_guard_truncate"

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
            "semantic_success": semantic_success,
            "summary": summary,
            "structured": structured,
            "raw_chars": len(raw),
            "summary_chars": len(summary),
            "processed": True,
            "processor": processor,
            "context_usage_ratio": context_usage_ratio,
            **refs,
        }

    def _extract(self, tool: str, raw: str) -> tuple[Dict[str, Any], str, str]:
        if tool == "fetch_runbook":
            return self._extract_runbook(raw)
        if re.search(r"is not a valid tool|try one of \[", raw, re.IGNORECASE):
            return {
                "status": "invalid_tool",
                "tool": tool,
                "raw_preview": raw[:1000],
            }, self._generic_summary(tool, raw), "invalid_tool"
        if re.search(r"command failed|error from server|the server doesn't have a resource type|notfound|not found", raw, re.IGNORECASE):
            return {
                "status": "command_failed",
                "tool": tool,
                "raw_preview": raw[:1000],
            }, self._generic_summary(tool, raw), "generic_failure"
        if re.search(r"^\s*no resources found", raw, re.IGNORECASE):
            return {
                "status": "empty",
                "tool": tool,
                "raw_preview": raw[:1000],
            }, "工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。", "generic_empty"

        if tool == "kubectl_events":
            return self._extract_events(raw)
        if tool == "kubectl_describe":
            return self._extract_describe(raw)
        if tool == "kubectl_get_yaml":
            return self._extract_yaml(raw)
        if tool == "kubectl_run_image":
            return self._extract_run_image(raw)
        if tool == "run_bash_command":
            return self._extract_command_result(tool, raw)
        if tool in {"execute_prometheus_instant_query", "execute_prometheus_range_query"}:
            return self._extract_prometheus_result(tool, raw)
        if tool in self.LOG_TOOLS:
            return self._extract_logs(tool, raw)
        if tool in {"kubectl_get_by_kind_in_cluster", "kubectl_get_by_kind_in_namespace", "kubernetes_tabular_query"}:
            if self._looks_like_secret_table(raw):
                return self._extract_secret_table(tool, raw)
            return self._extract_table(tool, raw)
        if tool == "kubernetes_jq_query":
            return self._extract_jq(raw)

        if tool in self.MEDIUM_TOOLS and len(raw) <= self.max_observation_chars:
            return {"status": "kept_small_output"}, raw, "passthrough"
        return {"status": "generic_summary"}, self._generic_summary(tool, raw), "generic"

    def _extract_runbook(self, raw: str) -> tuple[Dict[str, Any], str, str]:
        if re.match(r"^\s*Error:\s*Runbook\b", raw or "", re.IGNORECASE):
            return {
                "status": "command_failed",
                "tool": "fetch_runbook",
                "raw_preview": raw[:1000],
            }, self._generic_summary("fetch_runbook", raw), "runbook"

        title = None
        match = re.search(r"^\s*#\s+(.+)$", raw or "", re.MULTILINE)
        if match:
            title = match.group(1).strip()
        return {
            "status": "runbook_loaded",
            "title": title,
            "raw_chars": len(raw or ""),
        }, raw, "runbook"

    @staticmethod
    def _attach_runbook_metadata(structured: Dict[str, Any], tool_args: Dict[str, Any]) -> None:
        runbook_id = str((tool_args or {}).get("runbook_id") or "").strip()
        if not runbook_id:
            return
        structured["runbook_id"] = runbook_id
        structured["runbook_name"] = runbook_id[:-3] if runbook_id.endswith(".md") else runbook_id

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
        if re.search(r"command failed|error from server|notfound|not found", raw, re.IGNORECASE):
            return {"status": "command_failed", "raw_preview": raw[:1000]}, self._generic_summary("kubectl_describe", raw), "k8s_describe"

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
        columns = re.split(r"\s{2,}|\t+", header.strip())
        status_indexes = {
            idx for idx, column in enumerate(columns)
            if column.upper() in {"READY", "STATUS", "REASON", "PHASE"}
        }
        pure_status_indexes = {
            idx for idx, column in enumerate(columns)
            if column.upper() in {"STATUS", "REASON", "PHASE"}
        }
        endpoint_indexes = {
            idx for idx, column in enumerate(columns)
            if column.upper() in {"ENDPOINTS"}
        }
        abnormal = [
            ln for ln in lines[1:]
            if self._table_row_is_abnormal(ln, status_indexes, pure_status_indexes, endpoint_indexes)
        ]
        status_counts: Dict[str, int] = {}
        for ln in lines[1:]:
            for status in re.findall(
                r"\b(Running|Pending|Failed|Succeeded|CrashLoopBackOff|ImagePullBackOff|"
                r"ErrImagePull|OOMKilled|Evicted|NotReady|Ready|Terminating|Unknown|Error)\b",
                ln,
            ):
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

    @staticmethod
    def _looks_like_secret_table(raw: str) -> bool:
        lines = [ln for ln in (raw or "").splitlines() if ln.strip()]
        if not lines:
            return False
        header = lines[0].upper()
        if not all(col in header for col in ["NAME", "TYPE", "DATA", "AGE"]):
            return False
        body = "\n".join(lines[1:]).lower()
        return bool(re.search(r"\bkubernetes\.io/|opaque|helm\.sh/release\.v1", body))

    def _extract_secret_table(self, tool: str, raw: str) -> tuple[Dict[str, Any], str, str]:
        base_structured, base_summary, processor = self._extract_table(tool, raw)
        rows = base_structured.get("selected_rows") or []
        if not rows and base_structured.get("status") != "table_summarized":
            return base_structured, base_summary, processor

        docker_secret_rows = []
        docker_like_rows = []
        for row in rows:
            lowered = row.lower()
            if "kubernetes.io/dockerconfigjson" in lowered or "kubernetes.io/dockercfg" in lowered:
                docker_secret_rows.append(row)
            elif any(keyword in lowered for keyword in ["docker", "registry", "pull", "xnet-bmcs"]):
                docker_like_rows.append(row)

        structured = {
            **base_structured,
            "resource_kind": "Secret",
            "docker_secret_count": len(docker_secret_rows),
            "docker_like_rows": docker_like_rows[:20],
            "docker_secret_rows": docker_secret_rows[:20],
        }
        lines = [
            f"{tool} Secret 表摘要: rows={base_structured.get('row_count', 0)} abnormal={base_structured.get('abnormal_count', 0)}",
            f"docker_secret_count: {len(docker_secret_rows)}",
        ]
        if docker_secret_rows:
            lines.append("# kubernetes.io/dockerconfigjson/dockercfg Secret")
            lines.extend(docker_secret_rows[:20])
        else:
            lines.append("未发现 type 为 kubernetes.io/dockerconfigjson 或 kubernetes.io/dockercfg 的 Secret。")
        if docker_like_rows:
            lines.append("# 名称疑似与镜像拉取相关但类型不一定有效")
            lines.extend(docker_like_rows[:20])
        lines.append("# 全量 Secret 行已落盘到 raw_ref，selected_rows 已落盘到 structured_ref。")
        return structured, "\n".join(lines), "k8s_secret_table"

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
        if re.search(r"command failed|error from server|notfound|not found", raw, re.IGNORECASE):
            structured = {"status": "command_failed", "raw_preview": raw[:1000]}
            summary = self._generic_summary("kubectl_get_yaml", raw)
            return structured, summary, "k8s_yaml"

        try:
            doc = yaml.safe_load(raw) or {}
        except Exception as exc:
            structured = {"status": "yaml_parse_failed", "error": str(exc)}
            return structured, self._legacy_yaml_summary(raw), "k8s_yaml"

        if not isinstance(doc, dict):
            structured = {"status": "yaml_non_mapping", "type": type(doc).__name__}
            return structured, self._legacy_yaml_summary(raw), "k8s_yaml"

        kind = doc.get("kind")
        if kind == "Pod":
            return self._extract_pod_yaml(doc)
        if kind == "Secret":
            return self._extract_secret_yaml(doc)

        metadata = doc.get("metadata") if isinstance(doc.get("metadata"), dict) else {}
        structured = {
            "status": "yaml_summarized",
            "kind": kind,
            "name": metadata.get("name"),
            "namespace": metadata.get("namespace"),
        }
        lines = [
            "kubectl_get_yaml 关键字段摘要:",
            f"kind: {kind}",
            f"name: {metadata.get('name')}",
            f"namespace: {metadata.get('namespace')}",
        ]
        return structured, "\n".join(lines), "k8s_yaml"

    def _extract_pod_yaml(self, doc: Dict[str, Any]) -> tuple[Dict[str, Any], str, str]:
        metadata = doc.get("metadata") if isinstance(doc.get("metadata"), dict) else {}
        spec = doc.get("spec") if isinstance(doc.get("spec"), dict) else {}
        status = doc.get("status") if isinstance(doc.get("status"), dict) else {}
        labels = metadata.get("labels") if isinstance(metadata.get("labels"), dict) else {}
        annotations = metadata.get("annotations") if isinstance(metadata.get("annotations"), dict) else {}
        diagnostic_annotations = {
            str(key): value
            for key, value in annotations.items()
            if str(key).startswith(("aiops.", "robusta.", "kubernetes.io/change-cause"))
        }

        image_pull_secrets_raw = spec.get("imagePullSecrets")
        image_pull_secrets = [
            item.get("name")
            for item in image_pull_secrets_raw
            if isinstance(item, dict) and item.get("name")
        ] if isinstance(image_pull_secrets_raw, list) else []

        containers = []
        for container in spec.get("containers") or []:
            if not isinstance(container, dict):
                continue
            containers.append({
                "name": container.get("name"),
                "image": container.get("image"),
                "imagePullPolicy": container.get("imagePullPolicy"),
                "resources": container.get("resources") or {},
            })

        init_containers = []
        for container in spec.get("initContainers") or []:
            if not isinstance(container, dict):
                continue
            init_containers.append({
                "name": container.get("name"),
                "image": container.get("image"),
                "imagePullPolicy": container.get("imagePullPolicy"),
            })

        container_statuses = []
        for item in status.get("containerStatuses") or []:
            if not isinstance(item, dict):
                continue
            state = item.get("state") if isinstance(item.get("state"), dict) else {}
            last_state = item.get("lastState") if isinstance(item.get("lastState"), dict) else {}
            container_statuses.append({
                "name": item.get("name"),
                "ready": item.get("ready"),
                "restartCount": item.get("restartCount"),
                "image": item.get("image"),
                "imageID": item.get("imageID"),
                "waiting": state.get("waiting") if isinstance(state.get("waiting"), dict) else None,
                "terminated": state.get("terminated") if isinstance(state.get("terminated"), dict) else None,
                "lastTerminated": last_state.get("terminated") if isinstance(last_state.get("terminated"), dict) else None,
            })

        owner_refs = []
        for item in metadata.get("ownerReferences") or []:
            if isinstance(item, dict):
                owner_refs.append({"kind": item.get("kind"), "name": item.get("name")})

        volumes = []
        for volume in spec.get("volumes") or []:
            if not isinstance(volume, dict):
                continue
            volume_info = {"name": volume.get("name")}
            for source in ["configMap", "secret", "persistentVolumeClaim"]:
                if isinstance(volume.get(source), dict):
                    volume_info[source] = volume[source].get("name") or volume[source].get("claimName")
            volumes.append(volume_info)

        conditions = []
        for item in status.get("conditions") or []:
            if not isinstance(item, dict):
                continue
            conditions.append({
                "type": item.get("type"),
                "status": item.get("status"),
                "reason": item.get("reason"),
                "message": item.get("message"),
                "lastTransitionTime": item.get("lastTransitionTime"),
            })

        structured = {
            "status": "yaml_summarized",
            "kind": "Pod",
            "name": metadata.get("name"),
            "namespace": metadata.get("namespace"),
            "creationTimestamp": metadata.get("creationTimestamp"),
            "deletionTimestamp": metadata.get("deletionTimestamp"),
            "deletionGracePeriodSeconds": metadata.get("deletionGracePeriodSeconds"),
            "finalizers": metadata.get("finalizers") if isinstance(metadata.get("finalizers"), list) else [],
            "labels": labels,
            "diagnostic_annotations": diagnostic_annotations,
            "ownerReferences": owner_refs,
            "serviceAccountName": spec.get("serviceAccountName"),
            "nodeName": spec.get("nodeName"),
            "restartPolicy": spec.get("restartPolicy"),
            "terminationGracePeriodSeconds": spec.get("terminationGracePeriodSeconds"),
            "nodeSelector": spec.get("nodeSelector") if isinstance(spec.get("nodeSelector"), dict) else {},
            "tolerations": spec.get("tolerations") if isinstance(spec.get("tolerations"), list) else [],
            "affinity_present": isinstance(spec.get("affinity"), dict) and bool(spec.get("affinity")),
            "imagePullSecrets": image_pull_secrets,
            "imagePullSecrets_present": image_pull_secrets_raw is not None,
            "containers": containers,
            "initContainers": init_containers,
            "volumes": volumes,
            "phase": status.get("phase"),
            "reason": status.get("reason"),
            "message": status.get("message"),
            "conditions": conditions,
            "containerStatuses": container_statuses,
        }

        lines = [
            "kubectl_get_yaml 关键字段摘要:",
            "kind: Pod",
            f"name: {metadata.get('name')}",
            f"namespace: {metadata.get('namespace')}",
            f"creationTimestamp: {metadata.get('creationTimestamp')}",
            f"deletionTimestamp: {metadata.get('deletionTimestamp') or '<absent>'}",
            f"deletionGracePeriodSeconds: {metadata.get('deletionGracePeriodSeconds')}",
            "finalizers: " + (
                ", ".join(str(item) for item in structured["finalizers"])
                if structured["finalizers"] else "<none>"
            ),
            f"serviceAccountName: {spec.get('serviceAccountName')}",
            f"nodeName: {spec.get('nodeName')}",
            f"restartPolicy: {spec.get('restartPolicy')}",
            f"terminationGracePeriodSeconds: {spec.get('terminationGracePeriodSeconds')}",
            "imagePullSecrets: " + (", ".join(image_pull_secrets) if image_pull_secrets else "<absent>"),
            f"phase: {status.get('phase')}",
        ]
        if labels:
            label_facts = {
                key: labels.get(key)
                for key in sorted(labels)
                if key in {"app", "pod_abnormal_type", "expected_layer", "e2e-test"}
                or str(key).startswith(("aiops.", "robusta."))
            }
            if label_facts:
                lines.append("labels: " + ", ".join(f"{k}={v}" for k, v in label_facts.items()))
        if diagnostic_annotations:
            lines.append("diagnostic_annotations: " + ", ".join(
                f"{k}={v}" for k, v in sorted(diagnostic_annotations.items())
            ))
        if owner_refs:
            lines.append("ownerReferences: " + ", ".join(
                f"{item.get('kind')}/{item.get('name')}" for item in owner_refs
            ))
        if structured["nodeSelector"]:
            lines.append("nodeSelector: " + json.dumps(structured["nodeSelector"], ensure_ascii=False))
        if structured["tolerations"]:
            lines.append("tolerations_count: " + str(len(structured["tolerations"])))
        if structured["affinity_present"]:
            lines.append("affinity_present: True")
        if containers:
            lines.append("containers:")
            lines.extend(
                f"- {item.get('name')}: image={item.get('image')} imagePullPolicy={item.get('imagePullPolicy')}"
                for item in containers
            )
        if conditions:
            lines.append("conditions:")
            for item in conditions[:10]:
                detail = (
                    f"- {item.get('type')}: status={item.get('status')} "
                    f"reason={item.get('reason')}"
                )
                if item.get("message"):
                    detail += f" message={item.get('message')}"
                lines.append(detail)
        if container_statuses:
            lines.append("containerStatuses:")
            for item in container_statuses:
                waiting = item.get("waiting") or {}
                terminated = item.get("terminated") or item.get("lastTerminated") or {}
                reason = waiting.get("reason") or terminated.get("reason")
                message = waiting.get("message") or terminated.get("message")
                exit_code = terminated.get("exitCode")
                lines.append(
                    f"- {item.get('name')}: ready={item.get('ready')} restarts={item.get('restartCount')} "
                    f"reason={reason} exitCode={exit_code}"
                )
                if message:
                    lines.append(f"  message: {message}")
        if volumes:
            lines.append("volumes:")
            lines.extend(f"- {json.dumps(item, ensure_ascii=False)}" for item in volumes[:20])
        return structured, "\n".join(lines), "k8s_yaml"

    def _extract_secret_yaml(self, doc: Dict[str, Any]) -> tuple[Dict[str, Any], str, str]:
        metadata = doc.get("metadata") if isinstance(doc.get("metadata"), dict) else {}
        data = doc.get("data") if isinstance(doc.get("data"), dict) else {}
        data_keys = sorted(str(key) for key in data.keys())
        secret_type = doc.get("type")
        has_dockerconfigjson = any(key in data for key in [".dockerconfigjson", "dockerconfigjson"])
        docker_secret_type_valid = secret_type in {"kubernetes.io/dockerconfigjson", "kubernetes.io/dockercfg"}
        structured = {
            "status": "yaml_summarized",
            "kind": "Secret",
            "name": metadata.get("name"),
            "namespace": metadata.get("namespace"),
            "type": secret_type,
            "data_keys": data_keys,
            "has_dockerconfigjson": has_dockerconfigjson,
            "docker_secret_type_valid": docker_secret_type_valid,
        }
        lines = [
            "kubectl_get_yaml 关键字段摘要:",
            "kind: Secret",
            f"name: {metadata.get('name')}",
            f"namespace: {metadata.get('namespace')}",
            f"type: {secret_type}",
            "data_keys: " + (", ".join(data_keys) if data_keys else "<none>"),
            f"has_dockerconfigjson: {has_dockerconfigjson}",
            f"docker_secret_type_valid: {docker_secret_type_valid}",
        ]
        return structured, "\n".join(lines), "k8s_yaml"

    def _legacy_yaml_summary(self, raw: str) -> str:
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
        return "kubectl_get_yaml 关键字段摘要:\n" + "\n".join(keep[:120])

    def _table_row_is_abnormal(
        self,
        row: str,
        status_indexes: set[int],
        pure_status_indexes: set[int],
        endpoint_indexes: set[int],
    ) -> bool:
        cells = re.split(r"\s{2,}|\t+", row.strip())
        status_text = " ".join(
            cells[idx] for idx in status_indexes
            if idx < len(cells)
        )
        pure_status_text = " ".join(
            cells[idx] for idx in pure_status_indexes
            if idx < len(cells)
        )
        endpoint_text = " ".join(
            cells[idx] for idx in endpoint_indexes
            if idx < len(cells)
        )
        if endpoint_text and re.search(r"(^|\s)<none>($|\s)", endpoint_text, re.IGNORECASE):
            return True
        if pure_status_text:
            normalized = pure_status_text.strip().lower()
            if normalized in {"running", "completed", "succeeded", "ready", "bound", "active"}:
                return False
            return True
        return bool(re.search(
            r"CrashLoopBackOff|ImagePullBackOff|ErrImagePull|OOMKilled|Evicted|"
            r"Pending|Failed|Error|NotReady|Unknown|0/\d+",
            status_text,
            re.IGNORECASE,
        ))

    def _extract_run_image(self, raw: str) -> tuple[Dict[str, Any], str, str]:
        stripped = (raw or "").strip()
        try:
            parsed = json.loads(stripped) if stripped else {}
        except Exception:
            parsed = None

        if not isinstance(parsed, dict):
            return {"status": "run_image_unparsed"}, self._generic_summary("kubectl_run_image", raw), "k8s_run_image"

        success = parsed.get("success")
        stdout = (parsed.get("stdout") or "").strip()
        stderr = (parsed.get("stderr") or "").strip()
        returncode = parsed.get("returncode")
        merged = "\n".join(part for part in [stdout, stderr] if part)
        signals = []
        for pattern, label in [
            (r"timed out|deadlineexceeded|i/o timeout", "timeout"),
            (r"no such host|nxdomain|server can't find|temporary failure in name resolution", "dns"),
            (r"x509|certificate signed by unknown authority|tls", "tls"),
            (r"connection refused|no route to host|network is unreachable", "network"),
            (r"imagepullbackoff|errimagepull|failed to pull", "image_pull"),
        ]:
            if re.search(pattern, merged, re.IGNORECASE):
                signals.append(label)

        structured = {
            "status": "run_image_result",
            "success": success,
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
            "signals": signals,
        }
        summary_lines = [
            "kubectl_run_image 摘要:",
            f"success: {success}",
            f"returncode: {returncode}",
        ]
        if signals:
            summary_lines.append(f"signals: {', '.join(signals)}")
        if stdout:
            summary_lines.append(f"stdout: {stdout[:500]}")
        if stderr:
            summary_lines.append(f"stderr: {stderr[:1000]}")
        return structured, "\n".join(summary_lines), "k8s_run_image"

    def _extract_command_result(self, tool: str, raw: str) -> tuple[Dict[str, Any], str, str]:
        stripped = (raw or "").strip()
        try:
            parsed = json.loads(stripped) if stripped else {}
        except Exception:
            parsed = None
        if not isinstance(parsed, dict):
            return {"status": "command_unparsed"}, self._generic_summary(tool, raw), "command_result"
        stdout = (parsed.get("stdout") or "").strip()
        stderr = (parsed.get("stderr") or "").strip()
        structured = {
            "status": "command_result",
            "success": parsed.get("success"),
            "returncode": parsed.get("returncode"),
            "stdout_chars": len(stdout),
            "stderr_chars": len(stderr),
            "stdout_preview": stdout[:1000],
            "stderr_preview": stderr[:1000],
        }
        lines = [
            f"{tool} 输出摘要:",
            f"success: {parsed.get('success')}",
            f"returncode: {parsed.get('returncode')}",
        ]
        if stdout:
            lines.append(f"stdout: {stdout[:1000]}")
        if stderr:
            lines.append(f"stderr: {stderr[:1000]}")
        return structured, "\n".join(lines), "command_result"

    def _extract_logs(self, tool: str, raw: str) -> tuple[Dict[str, Any], str, str]:
        if re.search(r"command failed|error from server|notfound|not found", raw, re.IGNORECASE):
            return {"status": "command_failed", "raw_preview": raw[:1000]}, self._generic_summary(tool, raw), "k8s_logs"

        lines = [ln for ln in raw.splitlines() if ln.strip()]
        signal_patterns = (
            r"error|exception|traceback|panic|fatal|critical|failed|fail|warn|warning|"
            r"oom|killed|timeout|timed out|connection refused|permission denied|"
            r"no such file|not found|crash|segfault"
        )
        signal_lines = [ln for ln in lines if re.search(signal_patterns, ln, re.IGNORECASE)]
        selected = signal_lines[:40] or lines[-40:]
        structured = {
            "status": "logs_summarized",
            "line_count": len(lines),
            "signal_count": len(signal_lines),
            "selected_lines": selected,
        }
        summary_lines = [
            f"{tool} 日志摘要:",
            f"lines: {len(lines)}",
            f"signals: {len(signal_lines)}",
        ]
        if selected:
            summary_lines.append("关键日志:")
            summary_lines.extend(selected)
        else:
            summary_lines.append("日志为空；这是负向观察，不能证明应用无异常。")
        return structured, "\n".join(summary_lines), "k8s_logs"

    def _generic_summary(self, tool: str, raw: str) -> str:
        lines = [ln for ln in raw.splitlines() if ln.strip()]
        head = "\n".join(lines[:40])
        return f"{tool} 输出摘要: raw_chars={len(raw)} lines={len(lines)}\n{head}"

    def _extract_prometheus_result(self, tool: str, raw: str) -> tuple[Dict[str, Any], str, str]:
        try:
            payload = json.loads(raw or "{}")
        except Exception:
            payload = {}

        error = str(payload.get("error") or "").strip()
        error_type = str(payload.get("errorType") or "").strip()
        query = str(payload.get("query") or "").strip()
        url = str(payload.get("url") or "").strip()
        status = str(payload.get("status") or "").strip().lower()
        if error or error_type or status == "error" or re.search(r"\b(?:400|500)\s+Client Error|Bad Request", raw or "", re.IGNORECASE):
            message = error or error_type or raw[:1000]
            structured = {
                "status": "prometheus_error",
                "tool": tool,
                "error": message,
            }
            summary_lines = [f"{tool} 查询失败: {message}"]
            if error_type:
                structured["error_type"] = error_type
                summary_lines.append(f"Prometheus errorType: {error_type}")
            if query:
                structured["query"] = query
                summary_lines.append(f"PromQL: {query}")
            if url:
                structured["url"] = url
            return structured, "\n".join(summary_lines), "prometheus_error"

        result = ((payload.get("data") or {}).get("result") or []) if isinstance(payload, dict) else []
        result_count = len(result) if isinstance(result, list) else 0
        if result_count == 0:
            structured = {
                "status": "prometheus_empty",
                "tool": tool,
                "result_count": 0,
            }
            return structured, f"{tool} 执行成功但结果为空；这表示查询未命中数据，不能视为已采集到指标值。", "prometheus_empty"

        structured = {
            "status": "prometheus_result",
            "tool": tool,
            "result_count": result_count,
        }
        return structured, raw, "prometheus_result"

    @staticmethod
    def _is_semantically_successful(structured: Dict[str, Any], summary: str) -> bool:
        status = str((structured or {}).get("status", "")).lower()
        if status in {
            "empty",
            "command_failed",
            "yaml_parse_failed",
            "invalid_tool",
            "prometheus_error",
            "prometheus_empty",
            "run_image_result",
            "command_result",
        }:
            if status in {"run_image_result", "command_result"}:
                return bool((structured or {}).get("success") is True)
            return False
        if status == "runbook_loaded":
            return True
        text = summary or ""
        if not text.strip():
            return False
        if re.search(r"command failed|error from server|notfound|not found|工具返回为空", text, re.IGNORECASE):
            return False
        return True

    def _bound_summary(self, summary: str, raw: str) -> str:
        if len(summary) <= self.max_observation_chars:
            return summary
        suffix = f"\n... (已压缩/截断，原始 {len(raw)} 字符，完整内容见 raw_ref)"
        limit = max(0, self.max_observation_chars - len(suffix))
        return summary[:limit] + suffix
