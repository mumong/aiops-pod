import asyncio
import hashlib
import json
import os
import re
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

sys.path.insert(0, str(Path(__file__).resolve().parents[6]))

from app.core.workflow.fact_contract import (
    extract_fact_ledger_inputs_from_evidence_analysis,
    extract_fact_ledgers_from_evidence_analysis,
    normalize_fact_ledger,
    validate_rca_claims,
)
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode


OFFLINE_GUARD.install_client_guards()

SOURCE = Path("agent-loop/tasks/T007/attempts/A024/artifacts")
OUTPUT = Path("agent-loop/tasks/T007/attempts/A026/artifacts")


def load_inputs():
    final_report = (SOURCE / "final_report.md").read_text()
    conclusion_input = json.loads(
        (
            SOURCE
            / "context_archive/node_inputs/conclusion.input.json"
        ).read_text()
    )
    rca_output = json.loads(
        (
            SOURCE
            / "context_archive/node_outputs/rca.output.json"
        ).read_text()
    )
    return (
        final_report,
        conclusion_input,
        json.loads(rca_output["snapshot"]["rca_analysis"]),
    )


def reconcile_rca(evidence_analysis, raw_rca):
    validation_inputs = extract_fact_ledger_inputs_from_evidence_analysis(
        evidence_analysis
    )
    if not validation_inputs:
        validation_inputs = extract_fact_ledgers_from_evidence_analysis(
            evidence_analysis
        )
    ledgers = [
        ledger
        for value in validation_inputs
        if (ledger := normalize_fact_ledger(value)) is not None
    ]
    return validate_rca_claims(raw_rca, validation_inputs), ledgers


def replay_report(final_report, conclusion_input, reconciled_rca):
    node = ConclusionFormatterNode()
    structured_context = node._build_structured_diagnosis_context(
        conclusion_input["evidence_analysis"],
        json.dumps(reconciled_rca, ensure_ascii=False),
    )
    report = node._enforce_observability_dimension_table(
        final_report,
        structured_context,
    )
    report = node._sanitize_observability_evidence_refs(
        report,
        structured_context,
    )
    report = node._enforce_exact_topology_section(
        report,
        structured_context,
    )
    report = node._reconcile_legacy_report_limitations(
        report,
        structured_context,
    )
    report = node._enforce_metric_boundary_claims(
        report,
        structured_context,
    )
    report = node._enforce_evidence_scope_claims(
        report,
        structured_context,
    )
    report = node._enforce_entity_evidence_consistency(
        report,
        structured_context,
    )
    report = node._enforce_entity_identity_facts(
        report,
        conclusion_input["layer_analysis"],
        structured_context,
    )
    report = node._append_exact_k8s_signal_appendix(
        report,
        structured_context,
    )
    report = node._append_exact_observability_facts_appendix(
        report,
        structured_context,
    )
    return node._append_exact_topology_appendix(
        report,
        structured_context,
    )


def parse_remediation(report):
    section = report.split("## 🧩 结构化修复计划", 1)[1]
    match = re.search(
        r"```json\s*(\{.*?\})\s*```",
        section,
        re.DOTALL,
    )
    if match is None:
        raise AssertionError("structured remediation JSON fence not found")
    return json.loads(match.group(1))


def credential_hits(report):
    patterns = {
        "aws_access_key": r"\bAKIA[0-9A-Z]{16}\b",
        "openai_secret": r"\bsk-[A-Za-z0-9]{20,}\b",
        "bearer_token": r"\bBearer\s+[A-Za-z0-9._~+/=-]{20,}\b",
        "payment_token_value": (
            r"PAYMENT_GATEWAY_TOKEN\s*=\s*"
            r"(?!\.\.\.|<[^>]+>|\*+)"
            r"[\"']?[A-Za-z0-9._~+/=-]{8,}"
        ),
    }
    return {
        name: re.findall(pattern, report)
        for name, pattern in patterns.items()
        if re.search(pattern, report)
    }


def main():
    final_report, conclusion_input, raw_rca = load_inputs()
    reconciled_rca, ledgers = reconcile_rca(
        conclusion_input["evidence_analysis"],
        raw_rca,
    )
    rca_text = (
        json.dumps(
            reconciled_rca,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    OUTPUT.joinpath("a024-reconciled-rca.json").write_text(rca_text)

    report = replay_report(
        final_report,
        conclusion_input,
        reconciled_rca,
    )
    OUTPUT.joinpath("a024-offline-replayed-report.md").write_text(report)

    oom_log_values = [
        record.value
        for ledger in ledgers
        for record in ledger.records
        if record.dimension == "logging"
        and "trace-oom-api" in str(record.entity_name or "")
    ]
    ledger_allocated_mib = sorted({
        int(parsed["allocated_mib"])
        for value in oom_log_values
        if isinstance(value, str)
        for parsed in [json.loads(value)]
        if isinstance(parsed, dict) and "allocated_mib" in parsed
    })
    report_allocated_mib = sorted({
        int(value)
        for value in re.findall(
            r'allocated_mib\\?"\s*:\s*(\d+)',
            report,
        )
    })
    raw_rca_serialized = json.dumps(raw_rca, ensure_ascii=False)
    rca_serialized = json.dumps(reconciled_rca, ensure_ascii=False)
    remediation = parse_remediation(report)
    credentials = credential_hits(report)
    trace_ids = [
        "c1a2f2fbdf4bbbcf4edceb3453289673",
        "c18c1f49d70ee500220187abc3b58d8f",
    ]
    stale_rca_fragments = [
        "trace-oom-api 缺少日志",
        "OOM Pod 没有当前日志 Fact",
        "该 Pod 没有可用日志 Fact",
        "该 Pod 没有。",
        "不能为该 Pod 提供日志 message 原文",
    ]
    qualified_log_gaps = [
        "OOM 前日志",
        "日志中的时间戳",
        "日志缺少字段",
        "最近一次退出前日志窗口",
    ]
    offline_guard = OFFLINE_GUARD.audit()
    expected_guard_categories = set(OfflineReplayGuard.guarded_categories)
    offline_pass = (
        offline_guard["enforced"] is True
        and offline_guard["attempt_count"] == 0
        and offline_guard["attempts"] == []
        and set(offline_guard["guarded_categories"])
        == expected_guard_categories
    )
    checks = {
        "offline_guard_enforced": offline_guard["enforced"] is True,
        "offline_guard_no_external_attempts": (
            offline_guard["attempt_count"] == 0
            and offline_guard["attempts"] == []
        ),
        "offline_guard_categories_complete": (
            set(offline_guard["guarded_categories"])
            == expected_guard_categories
        ),
        "exact_shared_trace_ids_preserved": all(
            trace_id in report for trace_id in trace_ids
        ),
        "short_complete_trace_row_removed": (
            "| 完整 trace_id |" not in report
        ),
        "sampling_boundary_preserved": (
            "当前采样不能证明完整端到端调用链" in report
        ),
        "oom_deployment_identity_preserved": (
            "Deployment `aiops-traced-oom/trace-oom-api`" in report
        ),
        "deployment_gap_limited_to_podtemplate_resources": (
            "Deployment `aiops-traced-oom/trace-oom-api` "
            "的 PodTemplate/resources" in report
            and "Deployment 的准确名称及 PodTemplate" not in report
        ),
        "oom_58_60_62_log_facts_preserved": (
            {58, 60, 62}.issubset(report_allocated_mib)
            and {58, 60, 62}.issubset(ledger_allocated_mib)
        ),
        "rca_no_longer_denies_oom_logs": not any(
            stale in rca_serialized
            for stale in stale_rca_fragments
        ),
        "qualified_logging_gaps_preserved": all(
            fragment not in raw_rca_serialized
            or fragment in rca_serialized
            for fragment in qualified_log_gaps
        ),
        "rca_has_no_dangling_log_denial_fragments": (
            "没有。" not in rca_serialized
            and "不能为该 Pod 提供日志" not in rca_serialized
            and "但中的时间戳" not in rca_serialized
        ),
        "positive_direct_log_interpretation_preserved": (
            "同一 Pod 的直接日志，明确给出缺失配置和退出码 78"
            in rca_serialized
        ),
        "resource_limit_gap_preserved": any(
            token in report or token in rca_serialized
            for token in (
                "memory request/limit",
                "resource limits",
                "资源规格",
            )
        ),
        "continuous_memory_series_gap_preserved": any(
            token in report or token in rca_serialized
            for token in (
                "独立内存时间序列",
                "连续内存时序",
                "实际内存曲线",
            )
        ),
        "node_pressure_or_health_gap_preserved": (
            "没有 node2 异常的 direct Fact" in rca_serialized
            or "节点压力未知" in rca_serialized
        ),
        "sensitive_config_source_gap_preserved": (
            "Secret、ConfigMap、直接 env 或发布模板"
            in rca_serialized
            and "真实安全来源和值" in report
        ),
        "remediation_json_parseable": isinstance(remediation, dict),
        "credential_values_absent": not credentials,
    }
    failed = [
        name
        for name, passed in checks.items()
        if not passed
    ]
    audit = {
        "schema_version": "a024-offline-replay-audit-v2",
        "source_attempt": "A024",
        "offline_pass": offline_pass,
        "offline_guard": offline_guard,
        "inputs": [
            str(SOURCE / "final_report.md"),
            str(
                SOURCE
                / "context_archive/node_inputs/conclusion.input.json"
            ),
            str(
                SOURCE
                / "context_archive/node_outputs/rca.output.json"
            ),
        ],
        "fact_ledger_count": len(ledgers),
        "trace_ids": trace_ids,
        "oom_logging_record_count": len(oom_log_values),
        "oom_ledger_allocated_mib": ledger_allocated_mib,
        "oom_report_allocated_mib": report_allocated_mib,
        "checks": checks,
        "failed_checks": failed,
        "credential_hits": credentials,
        "remediation_top_level_keys": sorted(remediation),
        "sha256": {
            "report": hashlib.sha256(report.encode()).hexdigest(),
            "rca": hashlib.sha256(rca_text.encode()).hexdigest(),
        },
    }
    OUTPUT.joinpath("a024-replay-audit.json").write_text(
        json.dumps(
            audit,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True))
    if failed or not offline_pass:
        raise AssertionError(failed or ["offline_guard"])


if __name__ == "__main__":
    main()
