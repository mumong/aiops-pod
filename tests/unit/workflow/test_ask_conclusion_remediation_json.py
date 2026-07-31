import hashlib
import json
import os
import re
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import app.core.workflow.fact_contract as fact_contract_module
from app.core.remediation.plans import extract_remediation_plan
from app.core.prompts import (
    FACT_LEDGER_REMEDIATION_PLAN_PROMPT,
    REMEDIATION_PLAN_PROMPT,
)
from app.core.skills.models import Layer
from app.core.workflow.executor import WorkflowExecutor
from app.core.workflow.nodes.conclusion_formatter import ConclusionFormatterNode
from app.core.workflow.schemas import FactLedger, FactRecord


class _PlainAICall:
    def __init__(self, response: str):
        self.response = response

    def call_simple(self, *args, **kwargs):
        return self.response


def _node_with_response(response: str) -> ConclusionFormatterNode:
    node = ConclusionFormatterNode(holmes_service=SimpleNamespace())
    node.workflow_config_override = {}
    node.ai_call = _PlainAICall(response)
    return node


def _finalizer_evidence() -> str:
    return json.dumps(
        {
            "collection_summary": "计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%",
            "evidence_inventory": [
                {
                    "id": "pod-yaml",
                    "description": "获取 Terminating Pod YAML",
                    "tool": "kubectl_get_yaml",
                    "command": "kubectl get pod terminating-stuck -n aiops-e2e -o yaml",
                    "collected": True,
                    "raw_data": """
apiVersion: v1
kind: Pod
metadata:
  name: terminating-stuck
  namespace: aiops-e2e
  deletionTimestamp: "2026-06-01T01:00:00Z"
  finalizers:
  - aiops.e2e/hold
status:
  phase: Running
""",
                }
            ],
        },
        ensure_ascii=False,
    )


def _oom_and_unknown_secret_evidence() -> str:
    agent_facts = "\n".join(
        [
            "AIOPS_CASE case_id=oom status=case_collected abnormal_type=oomkilled",
            (
                "ENTITY entity=Pod "
                "aiops-traced-oom/trace-oom-api-598dcf5996-x6v6n"
            ),
            (
                "K8S_SIGNAL strength=strong observed="
                '"Last terminated state: business-api=OOMKilled exit=137"'
            ),
            (
                "METRIC metric=container_memory_working_set_bytes "
                "pod=trace-oom-api-598dcf5996-x6v6n start=3.3Mi "
                "max=70.9Mi last=70.9Mi limit=80.0Mi "
                "max_limit_ratio=0.8866"
            ),
            (
                "LOG event=allocate path=/allocate?mib=2 allocated_mib=62 "
                "trace_id=trace-oom"
            ),
            (
                "DEEPFLOW request=\"GET /allocate?mib=2\" response_code=200 "
                "trace_id=trace-oom"
            ),
            (
                "TEMPO trace_id=trace-oom span=\"GET /allocate\" "
                "aiops.allocated_mib.before=60 aiops.allocated_mib.after=62"
            ),
            (
                "AIOPS_CASE case_id=config status=case_collected "
                "abnormal_type=crashloopbackoff"
            ),
            (
                "ENTITY entity=Pod "
                "aiops-traced-config/trace-config-api-84bc7cb976-vgtl8"
            ),
            (
                "LOG event=config_missing message="
                '"required config PAYMENT_GATEWAY_TOKEN is missing"'
            ),
        ]
    )
    return json.dumps(
        {
            "collection_summary": "计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%",
            "tool_data": [
                {
                    "tool": "collect_aiops_case",
                    "agent_facts": agent_facts,
                    "agent_context": json.dumps(
                        {
                            "status": "case_collected",
                            "case_id": "oom-and-config",
                            "topology_summary": {
                                "entity_count": 2,
                                "edge_count": 1,
                            },
                            "dimension_details": {},
                        },
                        ensure_ascii=False,
                    ),
                }
            ],
        },
        ensure_ascii=False,
    )


_OPTIONAL_FACT_FIELDS = {
    "namespace",
    "entity_name",
    "strength",
    "unit",
    "timestamp",
    "start",
    "end",
    "metadata",
}


def _canonical_fact_id(record: dict) -> str:
    payload = {
        key: value
        for key, value in record.items()
        if key != "fact_id"
        and (key not in _OPTIONAL_FACT_FIELDS or value not in (None, {}, []))
    }
    payload["evidence_refs"] = sorted({
        str(ref)
        for ref in payload.get("evidence_refs", [])
        if str(ref or "").strip()
    })
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return "fact-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]


def _fact(
    *,
    entity_id: str,
    namespace: str,
    entity_name: str,
    attribute: str,
    value,
    evidence_ref: str,
    dimension: str = "kubernetes",
    fact_type: str = "state",
    entity_kind: str = "Pod",
    source_system: str = "kubernetes",
    directness: str = "direct",
    confidence: str = "high",
    strength: str = "strong",
    timestamp: str | None = None,
    unit: str | None = None,
) -> dict:
    record = {
        "entity_id": entity_id,
        "entity_kind": entity_kind,
        "namespace": namespace,
        "entity_name": entity_name,
        "dimension": dimension,
        "fact_type": fact_type,
        "attribute": attribute,
        "value": value,
        "unit": unit,
        "timestamp": timestamp,
        "source_system": source_system,
        "directness": directness,
        "confidence": confidence,
        "strength": strength,
        "evidence_refs": [evidence_ref],
    }
    record["fact_id"] = _canonical_fact_id(record)
    return record


def _ledger(case_id: str, scope_entity_ids: list[str], records: list[dict]) -> dict:
    return {
        "contract_version": "aiops.fact-ledger.v1",
        "case_id": case_id,
        "scope_entity_ids": scope_entity_ids,
        "records": records,
        "record_count": len(records),
        "truncated": False,
        "source": "mcp_canonical",
        "legacy_contract": False,
    }


def _fact_evidence(*ledgers: dict, extra_tool_data: list[dict] | None = None) -> str:
    tool_data = []
    for ledger in ledgers:
        item = {
            "tool": "collect_aiops_case",
            "fact_ledger": ledger,
        }
        if ledger.get("source") in {
            "mcp_canonical",
            "robusta_legacy_adapter",
        }:
            scope = next(
                (
                    str(value)
                    for value in ledger.get("scope_entity_ids") or []
                    if str(value).lower().startswith("k8s.pod:")
                ),
                "",
            )
            match = re.fullmatch(
                r"k8s\.pod:([^/]+)/([^:]+):(.+)",
                scope,
                flags=re.IGNORECASE,
            )
            if match:
                namespace, pod, pod_uid = match.groups()
                item.update({
                    "tool": "query_pod_logs",
                    "semantic_success": True,
                    "authority_context": {
                        "semantic_success": True,
                        "status": "query_succeeded",
                        "coverage": "present",
                        "source_system": str(
                            (
                                (ledger.get("records") or [{}])[0]
                            ).get("source_system")
                            or "legacy-source"
                        ),
                        "entity": {
                            "kind": "Pod",
                            "namespace": namespace,
                            "pod": pod,
                            "pod_uid": pod_uid,
                        },
                        "trusted_pod_uid": pod_uid,
                    },
                })
                decision = fact_contract_module.evaluate_report_authority(
                    ledger_input=ledger,
                    tool_item=item,
                )
                fact_contract_module.attach_internal_report_authority(
                    item,
                    ledger_input=ledger,
                    decision=decision,
                )
        tool_data.append(item)
    tool_data.extend(extra_tool_data or [])
    return json.dumps(
        {
            "collection_summary": (
                f"计划 {len(ledgers)} 项，实际采集 {len(ledgers)} 项，"
                "未采集 0 项，完整度 100%"
            ),
            "tool_data": tool_data,
        },
        ensure_ascii=False,
    )


def _rca_claim(
    *,
    diagnostic_status: str,
    root_cause_summary: str,
    hypotheses: list[dict],
    supporting_fact_ids: list[str],
    contradicting_fact_ids: list[str] | None = None,
    unknowns: list[str] | None = None,
    limitations: str = "",
) -> str:
    return json.dumps(
        {
            "diagnostic_status": diagnostic_status,
            "phenomenon": "当前 scope 中的 Pod 异常",
            "root_cause": root_cause_summary,
            "root_cause_summary": root_cause_summary,
            "supporting_fact_ids": supporting_fact_ids,
            "contradicting_fact_ids": contradicting_fact_ids or [],
            "unknowns": unknowns or [],
            "hypotheses": hypotheses,
            "confidence": 0.88 if diagnostic_status == "diagnosed" else 0.35,
            "confidence_reason": "引用当前 Fact Ledger 的直接事实",
            "limitations": limitations,
        },
        ensure_ascii=False,
    )


def _diagnosis_report(*, root_text: str, appendix_text: str = "") -> str:
    return f"""
## 诊断概览
模型生成的自然语言概览应保留。

## 现象描述
模型生成的现象叙述应保留。

## 根因分析
{root_text}

## 修复建议
当前先人工复核。

{appendix_text}
""".strip()


def _report_with_remediation_plan(plan: dict) -> str:
    return (
        _diagnosis_report(root_text="模型声称 finalizer 已确认。")
        + "\n\n## 结构化修复计划\n```json\n"
        + json.dumps(plan, ensure_ascii=False, indent=2)
        + "\n```\n"
    )


def _finalizer_plan(
    *,
    entity_id: str,
    namespace: str,
    pod: str,
    supporting_fact_ids: list[str],
    resource_form: str = "pod",
) -> dict:
    execute_target = (
        f"pod/{pod}"
        if resource_form == "pod/name"
        else f"{resource_form} {pod}"
    )
    return {
        "remediation_available": True,
        "fix_type": "remove_finalizer",
        "risk_level": "medium",
        "requires_human_approval": True,
        "issue_groups": [
            {
                "group_id": "g1",
                "problem_type": "TerminatingStuck",
                "target": f"{namespace}/pod/{pod}",
                "target_entity_id": entity_id,
                "auto_fixable": True,
                "strategy": "移除当前 Pod 已确认阻塞的 finalizer",
            }
        ],
        "basis": supporting_fact_ids,
        "actions": [
            {
                "id": "remove-finalizer-g1",
                "type": "kubectl_patch",
                "group_id": "g1",
                "target_issue": "TerminatingStuck",
                "target_entity_id": entity_id,
                "supporting_fact_ids": supporting_fact_ids,
                "description": "移除当前 Pod finalizers",
                "risk": "medium",
                "dry_run_command": f"kubectl get pod {pod} -n {namespace} -o yaml",
                "execute_command": (
                    f"kubectl patch {execute_target} -n {namespace} "
                    "-p '{\"metadata\":{\"finalizers\":null}}' --type=merge"
                ),
                "verify_command": f"kubectl get pod {pod} -n {namespace}",
            }
        ],
        "stop_conditions": ["事实不再显示 deletionTimestamp 与非空 finalizers"],
    }


def _deployment_patch_plan(
    *,
    entity_id: str,
    supporting_fact_ids: list[str],
) -> dict:
    return {
        "remediation_available": True,
        "fix_type": "patch_workload_resources",
        "risk_level": "medium",
        "requires_human_approval": True,
        "issue_groups": [
            {
                "group_id": "g1",
                "problem_type": "GenericWorkloadIssue",
                "target": "demo/deployment/api",
                "target_entity_id": entity_id,
                "auto_fixable": True,
                "strategy": "patch replicas",
            }
        ],
        "basis": supporting_fact_ids,
        "actions": [
            {
                "id": "patch-deployment-g1",
                "type": "kubectl_patch",
                "group_id": "g1",
                "target_entity_id": entity_id,
                "supporting_fact_ids": supporting_fact_ids,
                "description": "Patch deployment replicas.",
                "risk": "medium",
                "dry_run_command": (
                    "kubectl get deployment api -n demo -o yaml"
                ),
                "execute_command": (
                    "kubectl patch deployment api -n demo "
                    "-p '{\"spec\":{\"replicas\":2}}' --type=merge"
                ),
                "verify_command": (
                    "kubectl rollout status deployment/api -n demo "
                    "--timeout=60s"
                ),
            }
        ],
        "stop_conditions": [],
    }


def _execute_fact_bound_plan(
    *,
    plan_data: dict,
    entity_id: str,
    records: list[dict],
    layer: Layer = Layer.L2,
    diagnostic_status: str = "diagnosed",
    claim_supporting_fact_ids: list[str] | None = None,
):
    supporting_fact_ids = [record["fact_id"] for record in records]
    claim_fact_ids = claim_supporting_fact_ids or supporting_fact_ids
    claim = _rca_claim(
        diagnostic_status=diagnostic_status,
        root_cause_summary="same-entity candidate",
        hypotheses=[
            {
                "hypothesis_id": "hyp-bound-action",
                "entity_id": entity_id,
                "summary": "same-entity candidate",
                "supporting_fact_ids": claim_fact_ids,
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.9,
            }
        ],
        supporting_fact_ids=claim_fact_ids,
    )
    node = _node_with_response(_report_with_remediation_plan(plan_data))
    conclusion = node.execute(
        {
            "question": "为什么目标实体异常？",
            "layer": layer,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-bound-action", [entity_id], records)
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]
    return extract_remediation_plan(conclusion)


_ACTION_SPECIFIC_FACT_CASES = [
    (
        "delete",
        "kubectl delete deployment api -n demo",
        "lifecycle.desired_state",
        "absent",
    ),
    (
        "patch",
        (
            "kubectl patch deployment api -n demo "
            "-p '{\"spec\":{\"replicas\":2}}' --type=merge"
        ),
        "spec.replicas",
        2,
    ),
    (
        "scale",
        "kubectl scale deployment api -n demo --replicas=2",
        "spec.replicas",
        2,
    ),
    (
        "set_resources",
        (
            "kubectl set resources deployment/api -n demo "
            "--containers=api --limits=memory=128Mi "
            "--requests=memory=64Mi"
        ),
        "spec.template.spec.containers",
        [
            {
                "name": "api",
                "resources": {
                    "limits": {"memory": "128Mi"},
                    "requests": {"memory": "64Mi"},
                },
            }
        ],
    ),
    (
        "set_image",
        (
            "kubectl set image deployment/api "
            "api=example.invalid/api:v2 -n demo"
        ),
        "spec.template.spec.containers",
        {
            "name": "api",
            "image": "example.invalid/api:v2",
        },
    ),
    (
        "set_env",
        (
            "kubectl set env deployment/api "
            "FEATURE_FLAG=enabled --containers=api -n demo"
        ),
        "spec.template.spec.containers",
        [
            {
                "name": "api",
                "env": [{"name": "FEATURE_FLAG", "value": "enabled"}],
            }
        ],
    ),
    (
        "rollout_restart",
        "kubectl rollout restart deployment/api -n demo",
        "status.rollout.restart_required",
        True,
    ),
]


def test_fact_ledger_report_renders_validated_facts_and_appendix_deterministically():
    entity_id = "k8s.pod:demo/api:uid-api"
    metric = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        dimension="metrics",
        fact_type="measurement",
        attribute="container_memory_working_set_bytes",
        value={"observed": 81234567, "display": "77.47Mi"},
        unit="By",
        source_system="prometheus",
        evidence_ref="metric:api-memory",
        timestamp="2026-07-16T01:02:03Z",
    )
    log = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        dimension="logging",
        fact_type="log",
        attribute="log.message",
        value={
            "message": "required config PAYMENT_GATEWAY_TOKEN is missing",
            "trace_id": "trace-valid-1234567890",
        },
        source_system="elasticsearch",
        evidence_ref="log:api-current",
        timestamp="2026-07-16T01:02:04Z",
    )
    topology = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        entity_kind="Pod",
        dimension="topology",
        fact_type="relationship",
        attribute="topology.relationship",
        value={
            "source": {"entity_id": entity_id, "kind": "Pod"},
            "relation": "owned_by",
            "target": {
                "entity_id": "k8s.replicaset:demo/api-rs:uid-rs",
                "kind": "ReplicaSet",
            },
        },
        source_system="kubernetes",
        evidence_ref="topology:api-owner",
    )
    contradiction = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        attribute="status.ready",
        value=False,
        evidence_ref="k8s:api-ready",
        timestamp="2026-07-16T01:02:05Z",
    )
    records = [metric, log, topology, contradiction]
    ledger = _ledger("case-api", [entity_id], records)
    support_ids = [metric["fact_id"], log["fact_id"], topology["fact_id"]]
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="当前事实支持配置缺失根因候选",
        hypotheses=[
            {
                "hypothesis_id": "hyp-api",
                "entity_id": entity_id,
                "summary": "配置缺失导致当前 Pod 启动失败",
                "supporting_fact_ids": support_ids,
                "contradicting_fact_ids": [contradiction["fact_id"]],
                "unknowns": ["缺少修复后的恢复验证"],
                "confidence": 0.88,
            }
        ],
        supporting_fact_ids=support_ids,
        contradicting_fact_ids=[contradiction["fact_id"]],
        unknowns=["缺少正常业务基线"],
        limitations="尚未执行任何修复。",
    )
    response = _diagnosis_report(
        root_text="模型错误地改写为另一个根因。",
        appendix_text=(
            "## 机器可核验附录\n"
            "invented_value=999Mi unknown_ref=ref-invented trace_id=trace-invented"
        ),
    )
    node = _node_with_response(response)
    state = {
        "question": "为什么 api Pod 异常？",
        "layer": Layer.L2,
        "layer_analysis": "{}",
        "evidence_analysis": _fact_evidence(ledger),
        "rca_analysis": claim,
        "thinking_events": [],
    }

    first = node.execute(state)["conclusion"]
    second = node.execute(state)["conclusion"]

    assert first == second
    assert "模型生成的自然语言概览应保留" not in first
    assert "模型生成的现象叙述应保留" not in first
    assert "权威结论仅由 validated FactRecords 及其引用确定" in first
    assert "模型错误地改写为另一个根因" not in first
    assert "**诊断状态**: `diagnosed`" in first
    assert "当前事实支持配置缺失根因候选" not in first
    assert "配置缺失导致当前 Pod 启动失败" not in first
    assert "缺少正常业务基线" not in first
    assert "尚未执行任何修复" not in first
    for record in records:
        assert record["fact_id"] in first
    assert "81234567" in first
    assert "77.47Mi" in first
    assert "required config PAYMENT_GATEWAY_TOKEN is missing" in first
    assert "trace-valid-1234567890" in first
    assert '"relation":"owned_by"' in first
    assert "metric:api-memory" in first
    assert "source_system=prometheus" in first
    assert "directness=direct" in first
    assert "confidence=high" in first
    assert "2026-07-16T01:02:03Z" in first
    assert "invented_value=999Mi" not in first
    assert "ref-invented" not in first
    assert "trace-invented" not in first


def test_fact_ledger_report_omits_unproven_model_rca_factual_text():
    entity_id = "k8s.pod:demo/api:uid-api"
    metric = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        dimension="metrics",
        fact_type="measurement",
        attribute="cpu.usage",
        value=0.42,
        unit="ratio",
        source_system="prometheus",
        evidence_ref="metric:cpu-real",
    )
    invented_fragments = [
        "CPU=99.9%",
        "trace_id=trace-invented",
        "ref=ref-invented",
        "Service --owns--> Pod",
        "k8s.pod:demo/invented:uid-invented",
    ]
    invented_text = " ".join(invented_fragments)
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary=invented_text,
        hypotheses=[
            {
                "hypothesis_id": "hyp-api",
                "entity_id": entity_id,
                "summary": invented_text,
                "supporting_fact_ids": [metric["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.99,
            }
        ],
        supporting_fact_ids=[metric["fact_id"]],
    )
    node = _node_with_response(
        _diagnosis_report(root_text="模型报告中的根因段也不可信。")
    )

    conclusion = node.execute(
        {
            "question": "为什么 api Pod 异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-api", [entity_id], [metric])
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]

    for fragment in invented_fragments:
        assert fragment not in conclusion
    assert metric["fact_id"] in conclusion
    assert "0.42" in conclusion
    assert "metric:cpu-real" in conclusion


def test_fact_ledger_report_keeps_inconclusive_and_excludes_unknown_references():
    entity_id = "k8s.pod:demo/api:uid-api"
    metric = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        dimension="metrics",
        fact_type="measurement",
        attribute="cpu.usage",
        value=0.42,
        unit="ratio",
        source_system="prometheus",
        evidence_ref="metric:cpu-real",
    )
    unknown_fact_id = "fact-unknown000000"
    claim = _rca_claim(
        diagnostic_status="inconclusive",
        root_cause_summary="当前只有根因候选，不能确认",
        hypotheses=[
            {
                "hypothesis_id": "hyp-api",
                "entity_id": entity_id,
                "summary": "CPU 变化可能相关但证据不足",
                "supporting_fact_ids": [metric["fact_id"], unknown_fact_id],
                "contradicting_fact_ids": [],
                "unknowns": ["缺少故障窗口日志"],
                "confidence": 0.35,
            }
        ],
        supporting_fact_ids=[metric["fact_id"], unknown_fact_id],
        unknowns=["缺少故障窗口日志"],
    )
    response = _diagnosis_report(
        root_text=(
            "已确认根因是 CPU 超过 99.9%，Trace trace-fake 与 "
            "Service --owns--> Pod 证明故障。"
        ),
        appendix_text=(
            "## 机器可核验附录\n"
            f"{unknown_fact_id} ref:unknown trace-fake Service --owns--> Pod"
        ),
    )
    node = _node_with_response(response)

    conclusion = node.execute(
        {
            "question": "为什么 api Pod 异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-api", [entity_id], [metric])
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]

    assert "**诊断状态**: `inconclusive`" in conclusion
    assert "未形成已确认根因" in conclusion
    assert "当前只有根因候选，不能确认" not in conclusion
    assert "CPU 变化可能相关但证据不足" not in conclusion
    assert "缺少故障窗口日志" not in conclusion
    assert "已确认根因是 CPU 超过 99.9%" not in conclusion
    assert unknown_fact_id not in conclusion
    assert "ref:unknown" not in conclusion
    assert "trace-fake" not in conclusion
    assert "Service --owns--> Pod" not in conclusion
    assert metric["fact_id"] in conclusion
    assert "metric:cpu-real" in conclusion


def test_invalid_inconclusive_legacy_ledger_uses_deterministic_read_only_report():
    entity_id = "k8s.pod:demo/api:uid-api"
    lifecycle = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        attribute="container.last_exit_code",
        value={"container": "api", "exit_code": 1},
        evidence_ref="kubernetes:describe",
    )
    legacy_ledger = _ledger(
        "case-legacy-invalid",
        [entity_id],
        [lifecycle],
    )
    legacy_ledger["source"] = "robusta_legacy_adapter"
    legacy_ledger["legacy_contract"] = True
    claim = json.loads(
        _rca_claim(
            diagnostic_status="inconclusive",
            root_cause_summary=(
                "Current facts are insufficient for a validated "
                "root-cause conclusion"
            ),
            hypotheses=[
                {
                    "hypothesis_id": "hyp-invalid",
                    "summary": "Unsupported candidate",
                    "supporting_fact_ids": ["fact-ffffffffffff"],
                    "contradicting_fact_ids": [],
                    "unknowns": [],
                    "confidence": 0.9,
                }
            ],
            supporting_fact_ids=["fact-ffffffffffff"],
            unknowns=["Fact reference validation failed"],
        )
    )
    claim["confidence"] = 0.35
    claim["claim_validation"] = {
        "valid": False,
        "diagnostic_status": "inconclusive",
        "valid_supporting_fact_ids": [],
        "valid_contradicting_fact_ids": [],
        "invalid_fact_ids": ["fact-ffffffffffff"],
        "reasons": ["unknown supporting fact reference"],
        "legacy_contract": True,
    }
    unsafe_model_report = """
## 诊断概览
诊断状态：diagnosed。置信度：高（90%）。Node Ready，网络和配置问题均已排除。

## 根因分析
根因已经锁定，需要将资源目标固定为 128Mi。

## 修复建议
立即执行 `kubectl set resources deployment/api -n demo --limits=memory=128Mi`。
"""
    node = _node_with_response(unsafe_model_report)

    conclusion = node.execute(
        {
            "question": "我的集群有什么问题？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(legacy_ledger),
            "rca_analysis": json.dumps(claim, ensure_ascii=False),
            "thinking_events": [],
        }
    )["conclusion"]

    assert "**诊断状态**: `inconclusive`" in conclusion
    assert "**RCA 置信度上限**: `35%`" in conclusion
    assert "diagnosed" not in conclusion
    assert "90%" not in conclusion
    assert "Node Ready" not in conclusion
    assert "网络和配置问题均已排除" not in conclusion
    assert "128Mi" not in conclusion
    assert "kubectl set resources" not in conclusion
    assert "remediation_available" in conclusion
    assert '"remediation_available": false' in conclusion
    assert lifecycle["fact_id"] in conclusion
    assert "kubernetes:describe" in conclusion


@pytest.mark.parametrize("legacy_contract", [False, True])
def test_inconclusive_without_incoming_validation_discards_all_model_narrative(
    legacy_contract,
):
    entity_id = "k8s.pod:demo/api:uid-api"
    lifecycle = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        attribute="container.restart_count",
        value={"container": "api", "restart_count": 7},
        unit="count",
        fact_type="measurement",
        evidence_ref="kubernetes:describe",
    )
    ledger = _ledger(
        f"case-inconclusive-{legacy_contract}",
        [entity_id],
        [lifecycle],
    )
    if legacy_contract:
        ledger["source"] = "robusta_legacy_adapter"
        ledger["legacy_contract"] = True
    claim = _rca_claim(
        diagnostic_status="inconclusive",
        root_cause_summary="当前事实不足以确认根因",
        hypotheses=[
            {
                "hypothesis_id": "hyp-api",
                "entity_id": entity_id,
                "summary": "重启次数需要结合更多事实",
                "supporting_fact_ids": [lifecycle["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.35,
            }
        ],
        supporting_fact_ids=[lifecycle["fact_id"]],
    )
    adversarial_report = _diagnosis_report(
        root_text="根因段会被 Fact Ledger 重建。",
        appendix_text="""
## 影响评估
服务已完全中断。Node Ready，网络和配置问题均已排除。
建议将 memory limit 固定为 128Mi。
""".strip(),
    )
    node = _node_with_response(adversarial_report)

    conclusion = node.execute(
        {
            "question": "我的集群有什么问题？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(ledger),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]

    assert "**诊断状态**: `inconclusive`" in conclusion
    assert "**RCA 置信度上限**: `35%`" in conclusion
    assert lifecycle["fact_id"] in conclusion
    assert "kubernetes:describe" in conclusion
    assert "服务已完全中断" not in conclusion
    assert "Node Ready" not in conclusion
    assert "网络和配置问题均已排除" not in conclusion
    assert "128Mi" not in conclusion


def test_inconclusive_mixed_ledgers_preserve_non_equivalent_legacy_context():
    entity_id = "k8s.pod:demo/api:uid-api"
    canonical_state = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        attribute="pod.status",
        value={"status": "Running"},
        evidence_ref="canonical:pod-status",
    )
    legacy_resource = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        attribute="container.resource_limit.memory",
        value={"container": "business-api", "value": "80Mi"},
        unit="kubernetes_quantity",
        fact_type="configuration",
        evidence_ref="legacy:describe",
    )
    legacy_ledger = _ledger(
        "case-legacy-resource",
        [entity_id],
        [legacy_resource],
    )
    legacy_ledger["source"] = "robusta_legacy_adapter"
    legacy_ledger["legacy_contract"] = True
    claim = _rca_claim(
        diagnostic_status="inconclusive",
        root_cause_summary="当前事实不足以确认根因",
        hypotheses=[
            {
                "hypothesis_id": "hyp-api",
                "entity_id": entity_id,
                "summary": "只读事实待补证",
                "supporting_fact_ids": [canonical_state["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.35,
            }
        ],
        supporting_fact_ids=[canonical_state["fact_id"]],
    )
    node = _node_with_response(_diagnosis_report(root_text="不应保留。"))

    conclusion = node.execute(
        {
            "question": "我的集群有什么问题？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger(
                    "case-canonical",
                    [entity_id],
                    [canonical_state],
                ),
                legacy_ledger,
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]

    assert canonical_state["fact_id"] in conclusion
    assert legacy_resource["fact_id"] in conclusion
    assert "80Mi" in conclusion
    assert "legacy:describe" in conclusion


def test_inconclusive_mixed_ledgers_reject_blank_source_legacy_fact():
    entity_id = "k8s.pod:demo/api:uid-api"
    canonical_state = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        attribute="pod.status",
        value={"status": "Running"},
        evidence_ref="canonical:pod-status",
    )
    blank_source = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        attribute="container.resource_request.memory",
        value={"container": "business-api", "value": "33Mi"},
        unit="kubernetes_quantity",
        fact_type="configuration",
        source_system="   ",
        evidence_ref="legacy:blank-source",
    )
    legacy_ledger = _ledger(
        "case-legacy-blank-source",
        [entity_id],
        [blank_source],
    )
    legacy_ledger["source"] = "robusta_legacy_adapter"
    legacy_ledger["legacy_contract"] = True
    claim = _rca_claim(
        diagnostic_status="inconclusive",
        root_cause_summary="当前事实不足以确认根因",
        hypotheses=[
            {
                "hypothesis_id": "hyp-api",
                "entity_id": entity_id,
                "summary": "只读事实待补证",
                "supporting_fact_ids": [canonical_state["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.35,
            }
        ],
        supporting_fact_ids=[canonical_state["fact_id"]],
    )
    node = _node_with_response(_diagnosis_report(root_text="不应保留。"))

    conclusion = node.execute(
        {
            "question": "我的集群有什么问题？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger(
                    "case-canonical",
                    [entity_id],
                    [canonical_state],
                ),
                legacy_ledger,
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]

    assert canonical_state["fact_id"] in conclusion
    assert blank_source["fact_id"] not in conclusion
    assert "33Mi" not in conclusion
    assert "legacy:blank-source" not in conclusion


def test_inconclusive_merge_gate_rejects_validator_bypass_legacy_facts():
    entity_id = "k8s.pod:demo/api:uid-api"

    def bypass_fact(
        *,
        fact_id: str,
        value: str,
        source_system: str,
        evidence_refs: list[str],
    ) -> FactRecord:
        return FactRecord.model_construct(
            fact_id=fact_id,
            entity_id=entity_id,
            entity_kind="Pod",
            namespace="demo",
            entity_name="api",
            dimension="kubernetes",
            fact_type="configuration",
            attribute="container.resource_request.memory",
            value={"container": "business-api", "value": value},
            unit="kubernetes_quantity",
            timestamp=None,
            start=None,
            end=None,
            source_system=source_system,
            directness="direct",
            confidence="high",
            strength="strong",
            evidence_refs=evidence_refs,
            metadata={},
        )

    valid_80mi = bypass_fact(
        fact_id="fact-valid80mi",
        value="80Mi",
        source_system="kubernetes",
        evidence_refs=["legacy:valid-80mi"],
    )
    blank_source_33mi = bypass_fact(
        fact_id="fact-blank33mi",
        value="33Mi",
        source_system="   ",
        evidence_refs=["legacy:blank-source"],
    )
    empty_refs_48mi = bypass_fact(
        fact_id="fact-emptyrefs48mi",
        value="48Mi",
        source_system="kubernetes",
        evidence_refs=[],
    )
    legacy_ledger = FactLedger.model_construct(
        contract_version="aiops.fact-ledger.v1",
        case_id="case-legacy-publication-gate",
        scope_entity_ids=[entity_id],
        records=[
            valid_80mi,
            blank_source_33mi,
            empty_refs_48mi,
        ],
        record_count=3,
        truncated=False,
        source="robusta_legacy_adapter",
        legacy_contract=True,
    )

    merged = ConclusionFormatterNode._merge_inconclusive_fact_ledgers(
        all_ledgers=[legacy_ledger],
        canonical_ledgers=[],
    )
    serialized = json.dumps(
        [ledger.model_dump(mode="json") for ledger in merged],
        ensure_ascii=False,
        sort_keys=True,
    )

    assert len(merged) == 1
    assert merged[0].record_count == 1
    assert [record.fact_id for record in merged[0].records] == [
        valid_80mi.fact_id
    ]
    assert valid_80mi.fact_id in serialized
    assert "80Mi" in serialized
    assert "legacy:valid-80mi" in serialized
    assert blank_source_33mi.fact_id not in serialized
    assert "33Mi" not in serialized
    assert "legacy:blank-source" not in serialized
    assert empty_refs_48mi.fact_id not in serialized
    assert "48Mi" not in serialized
    assert '"evidence_refs": []' not in serialized


def test_inconclusive_mixed_ledgers_preserve_non_equivalent_legacy_value():
    entity_id = "k8s.pod:demo/api:uid-api"
    canonical_resource = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        attribute="container.resource_limit.memory",
        value={"container": "business-api", "value": "80Mi"},
        unit="kubernetes_quantity",
        fact_type="configuration",
        evidence_ref="canonical:resource-limit",
    )
    legacy_conflict = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        attribute="container.resource_limit.memory",
        value={"container": "business-api", "value": "128Mi"},
        unit="kubernetes_quantity",
        fact_type="configuration",
        evidence_ref="legacy:describe",
    )
    legacy_ledger = _ledger(
        "case-legacy-conflict",
        [entity_id],
        [legacy_conflict],
    )
    legacy_ledger["source"] = "robusta_legacy_adapter"
    legacy_ledger["legacy_contract"] = True
    claim = _rca_claim(
        diagnostic_status="inconclusive",
        root_cause_summary="当前事实不足以确认根因",
        hypotheses=[
            {
                "hypothesis_id": "hyp-api",
                "entity_id": entity_id,
                "summary": "只读事实待补证",
                "supporting_fact_ids": [canonical_resource["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.35,
            }
        ],
        supporting_fact_ids=[canonical_resource["fact_id"]],
    )
    node = _node_with_response(_diagnosis_report(root_text="不应保留。"))

    conclusion = node.execute(
        {
            "question": "我的集群有什么问题？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger(
                    "case-canonical-resource",
                    [entity_id],
                    [canonical_resource],
                ),
                legacy_ledger,
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]

    assert canonical_resource["fact_id"] in conclusion
    assert "80Mi" in conclusion
    assert legacy_conflict["fact_id"] in conclusion
    assert "128Mi" in conclusion
    assert "legacy:describe" in conclusion


def test_fact_report_fallback_sanitizes_archive_refs_and_passes_final_gate():
    entity_id = "k8s.pod:demo/api:uid-api"
    archive_root = "/tmp/aiops/reports/context_archives/"
    absolute_ref = (
        archive_root
        + "run-123/tools/001-evidence-kubectl_describe.raw.txt"
    )
    lifecycle = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        attribute="container.restart_count",
        value={"container": "api", "restart_count": 7},
        unit="count",
        fact_type="measurement",
        evidence_ref=absolute_ref,
    )
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="当前事实支持已诊断结论",
        hypotheses=[
            {
                "hypothesis_id": "hyp-api",
                "entity_id": entity_id,
                "summary": "当前事实支持已诊断结论",
                "supporting_fact_ids": [lifecycle["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.88,
            }
        ],
        supporting_fact_ids=[lifecycle["fact_id"]],
    )
    node = _node_with_response("# 阶段1：问题定位分析")
    node._format_with_template = lambda **kwargs: _diagnosis_report(
        root_text="fallback-template-used",
        appendix_text=f"## 其他信息\nref={absolute_ref}",
    )

    conclusion = node.execute(
        {
            "question": "我的集群有什么问题？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-archive-ref", [entity_id], [lifecycle])
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]

    assert archive_root not in conclusion
    assert "context-archive:run-123/tools/" in conclusion
    assert node._diagnosis_report_validation_errors(conclusion) == []


def test_fact_ledger_report_keeps_two_pod_facts_in_their_own_sections():
    entity_a = "k8s.pod:demo/api-a:uid-a"
    entity_b = "k8s.pod:demo/api-b:uid-b"
    fact_a = _fact(
        entity_id=entity_a,
        namespace="demo",
        entity_name="api-a",
        dimension="logging",
        fact_type="log",
        attribute="log.message",
        value={"message": "api-a-only-error"},
        source_system="elasticsearch",
        evidence_ref="log:api-a",
    )
    fact_b = _fact(
        entity_id=entity_b,
        namespace="demo",
        entity_name="api-b",
        dimension="logging",
        fact_type="log",
        attribute="log.message",
        value={"message": "api-b-only-error"},
        source_system="elasticsearch",
        evidence_ref="log:api-b",
    )
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="两个 Pod 各有独立根因候选",
        hypotheses=[
            {
                "hypothesis_id": "hyp-a",
                "entity_id": entity_a,
                "summary": (
                    "api-a 根因候选，但模型错误引用 "
                    "api-b-only-error"
                ),
                "supporting_fact_ids": [fact_a["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.9,
            },
            {
                "hypothesis_id": "hyp-b",
                "entity_id": entity_b,
                "summary": "api-b 根因候选",
                "supporting_fact_ids": [fact_b["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.9,
            },
        ],
        supporting_fact_ids=[fact_a["fact_id"], fact_b["fact_id"]],
    )
    node = _node_with_response(
        _diagnosis_report(root_text="模型把两个 Pod 的事实混在一起。")
    )

    conclusion = node.execute(
        {
            "question": "两个 Pod 为什么异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-a", [entity_a], [fact_a]),
                _ledger("case-b", [entity_b], [fact_b]),
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]

    section_a = conclusion.split(f"### `{entity_a}`", 1)[1].split(
        f"### `{entity_b}`",
        1,
    )[0]
    section_b = conclusion.split(f"### `{entity_b}`", 1)[1].split(
        "### 支持事实",
        1,
    )[0]
    assert fact_a["fact_id"] in section_a
    assert "api-a-only-error" in section_a
    assert fact_b["fact_id"] not in section_a
    assert "api-b-only-error" not in section_a
    assert fact_b["fact_id"] in section_b
    assert "api-b-only-error" in section_b
    assert fact_a["fact_id"] not in section_b
    assert "api-a-only-error" not in section_b


def test_fact_ledger_report_replaces_all_root_cause_sections_with_one_canonical_section():
    entity_id = "k8s.pod:demo/api:uid-api"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        attribute="status.phase",
        value="Failed",
        evidence_ref="k8s:api-status",
    )
    response = """
## 诊断概览
普通诊断概览应保留。

## 现象描述
普通现象描述应保留。

## 根因分析
FORGED_FIRST_ROOT

## 根因分析（重复）
FORGED_LATE_ROOT

## 修复建议
先人工复核。
""".strip()
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="模型根因候选",
        hypotheses=[
            {
                "hypothesis_id": "hyp-api",
                "entity_id": entity_id,
                "summary": "模型根因候选",
                "supporting_fact_ids": [fact["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.8,
            }
        ],
        supporting_fact_ids=[fact["fact_id"]],
    )
    node = _node_with_response(response)

    conclusion = node.execute(
        {
            "question": "为什么 api Pod 异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-api", [entity_id], [fact])
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]

    root_headings = [
        line
        for line in conclusion.splitlines()
        if line.startswith("##") and "根因分析" in line
    ]
    assert root_headings == ["## 🎯 根因分析"]
    assert "FORGED_FIRST_ROOT" not in conclusion
    assert "FORGED_LATE_ROOT" not in conclusion
    assert fact["fact_id"] in conclusion
    assert "普通诊断概览应保留" not in conclusion
    assert "普通现象描述应保留" not in conclusion
    assert "权威结论仅由 validated FactRecords" in conclusion


def test_fact_ledger_diagnostic_only_report_drops_model_guidance_and_commands():
    entity_id = "k8s.pod:demo/api:uid-api"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        attribute="status.phase",
        value="Failed",
        evidence_ref="k8s:api-status",
    )
    write_commands = [
        "kubectl apply -f /tmp/change.yaml",
        (
            "kubectl patch deployment api -n demo "
            "-p '{\"spec\":{\"replicas\":2}}' --type=merge"
        ),
        "kubectl delete pod api -n demo --force --grace-period=0",
        (
            "kubectl set image deployment/api "
            "api=example.invalid/new:latest -n demo"
        ),
        "kubectl scale deployment api -n demo --replicas=2",
        "kubectl rollout restart deployment/api -n demo",
        "kubectl taint nodes worker maintenance=true:NoSchedule",
    ]
    read_only_commands = [
        "kubectl get pod api -n demo",
        "kubectl describe pod api -n demo",
        "kubectl logs pod/api -n demo",
        "kubectl top pod api -n demo",
        (
            "kubectl rollout status deployment/api -n demo "
            "--timeout=60s"
        ),
    ]
    response = (
        _diagnosis_report(root_text="当前状态事实已确认。")
        + "\n\n人工修复指导应保留：请先评估变更风险并人工执行。\n\n"
        + "\n".join(f"- `{command}`" for command in write_commands)
        + "\n\n"
        + "\n".join(f"- `{command}`" for command in read_only_commands)
    )
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="当前状态事实已确认",
        hypotheses=[
            {
                "hypothesis_id": "hyp-api",
                "entity_id": entity_id,
                "summary": "当前状态事实已确认",
                "supporting_fact_ids": [fact["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.9,
            }
        ],
        supporting_fact_ids=[fact["fact_id"]],
    )
    node = _node_with_response(response)

    conclusion = node.execute(
        {
            "question": "为什么 api Pod 异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-api", [entity_id], [fact])
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]
    plan = extract_remediation_plan(conclusion)

    assert "人工修复指导应保留" not in conclusion
    for command in write_commands:
        assert command not in conclusion
    for command in read_only_commands:
        assert command not in conclusion
    assert "本报告不授权 Kubernetes 写操作" in conclusion
    assert conclusion.count("## 结构化修复计划") == 1
    assert plan is not None
    assert plan.remediation_available is False
    assert plan.fix_type == "manual_only"
    assert plan.requires_human_approval is True
    assert plan.actions == []


def test_fact_ledger_report_drops_all_model_shell_content():
    entity_id = "k8s.pod:demo/api:uid-api"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        attribute="status.phase",
        value="Failed",
        evidence_ref="k8s:api-status",
    )
    response = (
        _diagnosis_report(root_text="当前证据不足，继续人工诊断。")
        + "\n\n普通诊断文本和人工复核说明应保留。\n\n"
        + "正文 kubectl \\\n"
        + "  delete pod write-continuation -n demo\n"
        + "inline `kubectl --namespace demo delete pod write-inline`\n"
        + "```shell\n"
        + "$ KUBECTL --namespace demo DELETE pod write-upper\n"
        + "echo inspected; kubectl -n demo patch deployment write-chain "
        + "-p '{}'\n"
        + "kubectl -n demo rollout restart deployment/write-fenced\n"
        + "```\n\n"
        + "`kubectl --namespace demo get pod api`\n"
        + "`kubectl -n demo describe pod api`\n"
        + "`kubectl logs pod/api -n demo`\n"
        + "`kubectl top pod api -n demo`\n"
        + "`kubectl rollout status deployment/api -n demo`\n"
        + "`kubectl rollout history deployment/api -n demo`\n"
        + "`kubectl --context prod get pod api -n demo`\n"
    )
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="当前事实支持诊断结论",
        hypotheses=[
            {
                "hypothesis_id": "hyp-api",
                "entity_id": entity_id,
                "summary": "当前事实支持诊断结论",
                "supporting_fact_ids": [fact["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.88,
            }
        ],
        supporting_fact_ids=[fact["fact_id"]],
    )
    node = _node_with_response(response)

    conclusion = node.execute(
        {
            "question": "为什么 api Pod 异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-api", [entity_id], [fact])
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]

    for write_target in (
        "write-continuation",
        "write-inline",
        "write-upper",
        "write-chain",
        "write-fenced",
    ):
        assert write_target not in conclusion
    assert "kubectl rollout history deployment/api -n demo" not in conclusion
    assert "普通诊断文本和人工复核说明应保留" not in conclusion
    for read_only_command in (
        "kubectl --namespace demo get pod api",
        "kubectl -n demo describe pod api",
        "kubectl logs pod/api -n demo",
        "kubectl top pod api -n demo",
        "kubectl rollout status deployment/api -n demo",
        "kubectl --context prod get pod api -n demo",
    ):
        assert read_only_command not in conclusion


def test_fact_ledger_report_neutralizes_short_namespace_equals_writes_in_all_forms():
    entity_id = "k8s.pod:demo/api:uid-api"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        attribute="status.phase",
        value="Failed",
        evidence_ref="k8s:api-status",
    )
    response = (
        _diagnosis_report(root_text="当前证据不足，继续人工诊断。")
        + "\n\nkubectl -n=demo delete pod write-short-eq-body\n"
        + "inline `kubectl -n=demo patch deployment write-short-eq-inline "
        + "-p '{}'`\n"
        + "```shell\n"
        + "kubectl -n=demo scale deployment write-short-eq-fenced "
        + "--replicas=2\n"
        + "kubectl -n=demo get pod api\n"
        + "```\n"
    )
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="当前事实支持诊断结论",
        hypotheses=[
            {
                "hypothesis_id": "hyp-api",
                "entity_id": entity_id,
                "summary": "当前事实支持诊断结论",
                "supporting_fact_ids": [fact["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.88,
            }
        ],
        supporting_fact_ids=[fact["fact_id"]],
    )
    node = _node_with_response(response)

    conclusion = node.execute(
        {
            "question": "为什么 api Pod 异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-api", [entity_id], [fact])
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]

    for write_target in (
        "write-short-eq-body",
        "write-short-eq-inline",
        "write-short-eq-fenced",
    ):
        assert write_target not in conclusion
    assert "kubectl -n=demo get pod api" not in conclusion
    assert conclusion.count("```shell") == 0
    assert conclusion.count("```") % 2 == 0


def test_fact_ledger_report_drops_same_line_model_prose_with_write():
    entity_id = "k8s.pod:demo/api:uid-api"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        attribute="status.phase",
        value="Failed",
        evidence_ref="k8s:api-status",
    )
    response = (
        _diagnosis_report(root_text="当前证据不足，继续人工诊断。")
        + "\n\n请勿执行 kubectl delete pod write-prose -n demo；"
        + "尾部诊断结论应保留。\n"
        + "```shell\n"
        + "echo KEEP_FENCE_START\n"
        + "kubectl patch deployment write-fenced-prose -n demo -p '{}'\n"
        + "kubectl get pod api -n demo\n"
        + "echo KEEP_FENCE_END\n"
        + "```\n"
    )
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="当前事实支持诊断结论",
        hypotheses=[
            {
                "hypothesis_id": "hyp-api",
                "entity_id": entity_id,
                "summary": "当前事实支持诊断结论",
                "supporting_fact_ids": [fact["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.88,
            }
        ],
        supporting_fact_ids=[fact["fact_id"]],
    )
    node = _node_with_response(response)

    conclusion = node.execute(
        {
            "question": "为什么 api Pod 异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-api", [entity_id], [fact])
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]

    assert "write-prose" not in conclusion
    assert "write-fenced-prose" not in conclusion
    assert "尾部诊断结论应保留" not in conclusion
    assert "kubectl get pod api -n demo" not in conclusion
    assert "KEEP_FENCE_START" not in conclusion
    assert "KEEP_FENCE_END" not in conclusion
    assert conclusion.count("```shell") == 0
    assert conclusion.count("```") % 2 == 0


@pytest.mark.parametrize(
    ("separator", "trailing_text"),
    [
        ("；", "同行中文分号文本应保留"),
        ("。", "同行中文句号文本应保留"),
        ("！", "同行中文叹号文本应保留"),
        ("？", "同行中文问号文本应保留"),
        ("，", "同行中文逗号文本应保留"),
        ("：", "同行中文冒号文本应保留"),
    ],
)
def test_fact_ledger_report_drops_chinese_model_prose_after_write(
    separator,
    trailing_text,
):
    entity_id = "k8s.pod:demo/api:uid-api"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        attribute="status.phase",
        value="Failed",
        evidence_ref="k8s:api-status",
    )
    response = (
        _diagnosis_report(root_text="当前证据不足，继续人工诊断。")
        + "\n\nkubectl delete pod write-chinese-punctuation -n demo"
        + separator
        + trailing_text
        + "\n"
        + "```shell\n"
        + "kubectl get pod api -n demo\n"
        + "```\n"
    )
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="当前事实支持诊断结论",
        hypotheses=[
            {
                "hypothesis_id": "hyp-api",
                "entity_id": entity_id,
                "summary": "当前事实支持诊断结论",
                "supporting_fact_ids": [fact["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.88,
            }
        ],
        supporting_fact_ids=[fact["fact_id"]],
    )
    node = _node_with_response(response)

    conclusion = node.execute(
        {
            "question": "为什么 api Pod 异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-api", [entity_id], [fact])
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]

    assert "write-chinese-punctuation" not in conclusion
    assert trailing_text not in conclusion
    assert "kubectl get pod api -n demo" not in conclusion
    assert conclusion.count("```shell") == 0
    assert conclusion.count("```") % 2 == 0


def test_fact_ledger_report_removes_duplicate_structured_remediation_sections():
    entity_id = "k8s.pod:demo/api:uid-api"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        attribute="status.phase",
        value="Failed",
        evidence_ref="k8s:api-status",
    )
    empty_plan = {
        "remediation_available": False,
        "fix_type": "manual_only",
        "risk_level": "medium",
        "requires_human_approval": True,
        "issue_groups": [],
        "basis": [],
        "actions": [],
        "stop_conditions": [],
    }
    unauthorized_plan = {
        **empty_plan,
        "remediation_available": True,
        "actions": [
            {
                "id": "delete-api",
                "type": "kubectl_delete",
                "target_entity_id": entity_id,
                "supporting_fact_ids": ["fact-unknown000000"],
                "description": "Delete api.",
                "risk": "high",
                "execute_command": "kubectl delete pod api -n demo",
            }
        ],
    }
    response = (
        _diagnosis_report(root_text="当前状态事实。")
        + "\n\n## 结构化修复计划\n```json\n"
        + json.dumps(empty_plan, ensure_ascii=False)
        + "\n```\n\n## 结构化修复计划（备用）\n```json\n"
        + json.dumps(unauthorized_plan, ensure_ascii=False)
        + "\n```\n"
    )
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="当前状态事实",
        hypotheses=[
            {
                "hypothesis_id": "hyp-api",
                "entity_id": entity_id,
                "summary": "当前状态事实",
                "supporting_fact_ids": [fact["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.8,
            }
        ],
        supporting_fact_ids=[fact["fact_id"]],
    )
    node = _node_with_response(response)

    conclusion = node.execute(
        {
            "question": "为什么 api Pod 异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-api", [entity_id], [fact])
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]
    plan = extract_remediation_plan(conclusion)

    assert conclusion.count("## 结构化修复计划") == 1
    assert "kubectl delete pod api -n demo" not in conclusion
    assert plan is not None
    assert plan.remediation_available is False
    assert plan.actions == []


def test_fact_ledger_report_removes_all_model_remediation_objects():
    entity_id = "k8s.pod:demo/api:uid-api"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        attribute="status.phase",
        value="Failed",
        evidence_ref="k8s:api-status",
    )
    plans = [
        (
            "",
            {
                "remediation_available": True,
                "fix_type": "delete_pod",
                "actions": [
                    {
                        "id": "delete-newline",
                        "type": "kubectl_delete",
                        "execute_command": (
                            "kubectl\ndelete pod write-newline -n demo"
                        ),
                    }
                ],
            },
        ),
        (
            "## Structured Remediation Plan\n\n",
            {
                "remediation_available": True,
                "fix_type": "delete_pod",
                "actions": [
                    {
                        "id": "delete-tab",
                        "type": "kubectl_delete",
                        "execute_command": (
                            "kubectl\tdelete pod write-tab -n demo"
                        ),
                    }
                ],
            },
        ),
    ]
    leading_and_english = "\n\n".join(
        heading
        + "```json\n"
        + json.dumps(plan, ensure_ascii=False)
        + "\n```"
        for heading, plan in plans
    )
    unicode_space_plan = r"""
## Automated Action Contract

```json
{
  "remediation_available": true,
  "fix_type": "delete_pod",
  "actions": [
    {
      "id": "delete-unicode-space",
      "type": "kubectl_delete",
      "execute_command": "kubectl\u0020delete pod write-unicode-space -n demo"
    }
  ]
}
```
""".strip()
    response = (
        leading_and_english
        + "\n\n"
        + _diagnosis_report(root_text="当前状态事实。")
        + "\n\n"
        + unicode_space_plan
    )
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="当前状态事实",
        hypotheses=[
            {
                "hypothesis_id": "hyp-api",
                "entity_id": entity_id,
                "summary": "当前状态事实",
                "supporting_fact_ids": [fact["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.8,
            }
        ],
        supporting_fact_ids=[fact["fact_id"]],
    )
    node = _node_with_response(response)

    conclusion = node.execute(
        {
            "question": "为什么 api Pod 异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-api", [entity_id], [fact])
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]
    plan = extract_remediation_plan(conclusion)

    for target in (
        "write-newline",
        "write-tab",
        "write-unicode-space",
    ):
        assert target not in conclusion
    assert conclusion.count('"remediation_available"') == 1
    assert conclusion.count(
        '"remediation_contract": "fact-ledger-diagnostic-only-v1"'
    ) == 1
    assert plan is not None
    assert plan.remediation_available is False
    assert plan.fix_type == "manual_only"
    assert plan.actions == []


@pytest.mark.parametrize(
    ("envelope_shape", "fenced"),
    [
        ("dict", True),
        ("list", True),
        ("three_level", False),
        ("siblings", False),
    ],
)
def test_fact_ledger_report_removes_nested_remediation_envelopes(
    envelope_shape,
    fenced,
):
    entity_id = "k8s.pod:demo/api:uid-api"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        attribute="status.phase",
        value="Failed",
        evidence_ref="k8s:api-status",
    )

    def remediation_payload(suffix):
        return {
            "remediation_available": True,
            "fix_type": "delete_pod",
            "issue_groups": [
                {
                    "group_id": f"group-{suffix}",
                    "custom_model_field": f"custom-{suffix}",
                    "strategy": (
                        f"kubectl delete pod write-{suffix} -n demo"
                    ),
                }
            ],
            "actions": [
                {
                    "execute_command": (
                        f"kubectl delete pod write-{suffix} -n demo"
                    )
                }
            ],
        }

    if envelope_shape == "dict":
        envelope = {
            "dict-envelope-marker": {
                "payload": remediation_payload("dict")
            }
        }
    elif envelope_shape == "list":
        envelope = [
            {"list-envelope-marker": "remove-complete-list-fence"},
            {"payload": remediation_payload("list")},
        ]
    elif envelope_shape == "three_level":
        envelope = {
            "three-level-envelope-marker": [
                {
                    "level_two": {
                        "level_three": remediation_payload("three-level")
                    }
                }
            ]
        }
    else:
        envelope = {
            "sibling-envelope-marker": [
                {"payload": remediation_payload("sibling-one")},
                {"payload": remediation_payload("sibling-two")},
            ]
        }

    encoded_envelope = json.dumps(
        envelope,
        ensure_ascii=False,
        indent=2,
    )
    model_json = (
        f"```json\n{encoded_envelope}\n```"
        if fenced
        else f"Model JSON envelope:\n{encoded_envelope}"
    )
    ordinary_json = {
        "ordinary-envelope-marker": {
            "status": "retain-ordinary-json",
            "items": [{"name": "ordinary-sibling"}],
        }
    }
    response = (
        _diagnosis_report(root_text="当前状态事实。")
        + "\n\n"
        + model_json
        + "\n\n```json\n"
        + json.dumps(ordinary_json, ensure_ascii=False, indent=2)
        + "\n```\n"
    )
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="当前状态事实",
        hypotheses=[
            {
                "hypothesis_id": "hyp-api",
                "entity_id": entity_id,
                "summary": "当前状态事实",
                "supporting_fact_ids": [fact["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.8,
            }
        ],
        supporting_fact_ids=[fact["fact_id"]],
    )
    node = _node_with_response(response)

    conclusion = node.execute(
        {
            "question": "为什么 api Pod 异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-api", [entity_id], [fact])
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]
    plan = extract_remediation_plan(conclusion)

    assert f"{envelope_shape.replace('_', '-')}-envelope-marker" not in conclusion
    assert "custom_model_field" not in conclusion
    assert "ordinary-envelope-marker" not in conclusion
    assert "retain-ordinary-json" not in conclusion
    assert conclusion.count(
        '"remediation_contract": "fact-ledger-diagnostic-only-v1"'
    ) == 1
    for field in (
        '"remediation_available"',
        '"issue_groups"',
        '"actions"',
    ):
        assert conclusion.count(field) == 1
    assert plan is not None
    assert plan.remediation_available is False
    assert plan.fix_type == "manual_only"
    assert plan.actions == []


def test_fact_ledger_report_allowlists_commands_and_issue_group_fields():
    entity_id = "k8s.pod:demo/api:uid-api"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        attribute="status.phase",
        value="Failed",
        evidence_ref="k8s:api-status",
    )
    source_plan = {
        "remediation_available": False,
        "fix_type": "manual_only",
        "issue_groups": [
            {
                "group_id": "g1",
                "problem_type": "GenericWorkloadIssue",
                "target": "demo/pod/api",
                "auto_fixable": True,
                "strategy": (
                    "Execute kubectl delete pod issue-strategy -n demo "
                    "after review"
                ),
                "execute_command": (
                    "kubectl patch pod issue-custom -n demo -p '{}'"
                ),
                "custom_model_field": "must not survive",
            }
        ],
        "actions": [],
    }
    response = (
        _diagnosis_report(root_text="当前证据不足，继续人工诊断。")
        + "\n\nkubectl run write-run --image=busybox\n"
        + "inline `kubectl expose deployment write-expose --port=80`\n"
        + "```shell\n"
        + "kubectl autoscale deployment write-autoscale --min=1 --max=3\n"
        + "kubectl auth reconcile -f write-rbac.yaml\n"
        + "kubectl certificate approve write-csr\n"
        + "kubectl exec pod/write-exec -n demo -- touch /tmp/write\n"
        + "kubectl --context prod delete pod write-global -n demo\n"
        + "kubectl --context prod get pod api -n demo\n"
        + "kubectl rollout status deployment/api -n demo\n"
        + "```\n"
        + "```json\n"
        + r'{"note":"kubectl\u0020run write-json --image=busybox",'
        + r'"read":"kubectl\u0020describe pod api -n demo"}'
        + "\n```\n"
        + "\n## Remediation Details\n\n```json\n"
        + json.dumps(source_plan, ensure_ascii=False)
        + "\n```\n"
    )
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="当前事实支持诊断结论",
        hypotheses=[
            {
                "hypothesis_id": "hyp-api",
                "entity_id": entity_id,
                "summary": "当前事实支持诊断结论",
                "supporting_fact_ids": [fact["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.88,
            }
        ],
        supporting_fact_ids=[fact["fact_id"]],
    )
    node = _node_with_response(response)

    conclusion = node.execute(
        {
            "question": "为什么 api Pod 异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-api", [entity_id], [fact])
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]
    plan = extract_remediation_plan(conclusion)

    for target in (
        "write-run",
        "write-expose",
        "write-autoscale",
        "write-rbac",
        "write-csr",
        "write-exec",
        "write-global",
        "write-json",
        "issue-strategy",
        "issue-custom",
        "must not survive",
    ):
        assert target not in conclusion
    for model_command in (
        "kubectl --context prod get pod api -n demo",
        "kubectl rollout status deployment/api -n demo",
        "kubectl describe pod api -n demo",
    ):
        assert model_command not in conclusion
    assert plan is not None
    assert plan.issue_groups == []
    assert plan.remediation_available is False
    assert plan.fix_type == "manual_only"
    assert plan.actions == []


def test_fact_ledger_path_bypasses_legacy_fault_specific_report_helpers():
    entity_id = "k8s.pod:demo/api:uid-api"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        dimension="logging",
        fact_type="log",
        attribute="log.message",
        value={"message": "generic failure"},
        source_system="elasticsearch",
        evidence_ref="log:api",
    )
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="通用事实支持的根因候选",
        hypotheses=[
            {
                "hypothesis_id": "hyp-api",
                "entity_id": entity_id,
                "summary": "通用根因候选",
                "supporting_fact_ids": [fact["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.9,
            }
        ],
        supporting_fact_ids=[fact["fact_id"]],
    )
    node = _node_with_response(_diagnosis_report(root_text="模型根因。"))

    def _fail(*args, **kwargs):
        raise AssertionError("legacy fault-specific report helper must be bypassed")

    for name in (
        "_normalize_ask_remediation_plan",
        "_enforce_observability_dimension_table",
        "_sanitize_observability_evidence_refs",
        "_enforce_exact_topology_section",
        "_enforce_metric_boundary_claims",
        "_enforce_evidence_scope_claims",
        "_enforce_entity_evidence_consistency",
        "_enforce_entity_identity_facts",
        "_append_exact_k8s_signal_appendix",
        "_append_exact_observability_facts_appendix",
        "_append_exact_topology_appendix",
    ):
        setattr(node, name, _fail)

    conclusion = node.execute(
        {
            "question": "为什么 api Pod 异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-api", [entity_id], [fact])
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]

    assert "**报告合同**: `fact-ledger-authoritative-v1`" in conclusion


def test_no_fact_ledger_keeps_legacy_compatibility_path_and_marks_contract():
    node = _node_with_response(_diagnosis_report(root_text="legacy 根因候选。"))
    calls = []
    original = node._enforce_metric_boundary_claims

    def _record_legacy_call(*args, **kwargs):
        calls.append("metric-boundary")
        return original(*args, **kwargs)

    node._enforce_metric_boundary_claims = _record_legacy_call
    conclusion = node.execute(
        {
            "question": "为什么 Pod 异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": "{}",
            "rca_analysis": "{}",
            "thinking_events": [],
        }
    )["conclusion"]

    assert calls == ["metric-boundary"]
    assert "report_contract=legacy-compatibility" in conclusion


def test_fact_ledger_diagnostic_only_rejects_exact_finalizer_action():
    entity_id = "k8s.pod:demo/terminating-stuck:uid-current"
    deletion = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="terminating-stuck",
        attribute="metadata.deletionTimestamp",
        value="2026-07-16T01:00:00Z",
        evidence_ref="k8s:deletion-current",
    )
    finalizers = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="terminating-stuck",
        attribute="metadata.finalizers",
        value=["aiops.example/hold"],
        evidence_ref="k8s:finalizers-current",
    )
    support_ids = [deletion["fact_id"], finalizers["fact_id"]]
    plan_data = _finalizer_plan(
        entity_id=entity_id,
        namespace="demo",
        pod="terminating-stuck",
        supporting_fact_ids=support_ids,
    )
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="当前 Pod 删除被非空 finalizers 阻塞",
        hypotheses=[
            {
                "hypothesis_id": "hyp-current",
                "entity_id": entity_id,
                "summary": "当前 UID 的 deletionTimestamp 与 finalizers 同时存在",
                "supporting_fact_ids": support_ids,
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.95,
            }
        ],
        supporting_fact_ids=support_ids,
    )
    node = _node_with_response(_report_with_remediation_plan(plan_data))

    conclusion = node.execute(
        {
            "question": "为什么 Pod 一直 Terminating？",
            "layer": Layer.L1,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-current", [entity_id], [deletion, finalizers])
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]
    plan = extract_remediation_plan(conclusion)

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.fix_type == "manual_only"
    assert plan.requires_human_approval is True
    assert plan.actions == []
    assert "remediation_contract=fact-ledger-diagnostic-only-v1" in conclusion


@pytest.mark.parametrize(
    "case",
    [
        "cross_pod",
        "stale_uid",
        "missing_finalizer",
        "empty_finalizer",
        "empty_finalizer_text",
        "runbook_only",
    ],
)
def test_fact_bound_finalizer_action_rejects_unauthorized_evidence(case):
    current_entity = "k8s.pod:demo/terminating-stuck:uid-current"
    other_entity = "k8s.pod:demo/other-pod:uid-other"
    target_entity = current_entity
    ledgers = []
    hypotheses = []

    current_deletion = _fact(
        entity_id=current_entity,
        namespace="demo",
        entity_name="terminating-stuck",
        attribute="metadata.deletionTimestamp",
        value="2026-07-16T01:00:00Z",
        evidence_ref="k8s:deletion-current",
    )
    current_finalizers = _fact(
        entity_id=current_entity,
        namespace="demo",
        entity_name="terminating-stuck",
        attribute="metadata.finalizers",
        value=["aiops.example/hold"],
        evidence_ref="k8s:finalizers-current",
    )
    support_records = [current_deletion, current_finalizers]

    if case == "cross_pod":
        current_status = _fact(
            entity_id=current_entity,
            namespace="demo",
            entity_name="terminating-stuck",
            attribute="status.phase",
            value="Terminating",
            evidence_ref="k8s:status-current",
        )
        other_deletion = _fact(
            entity_id=other_entity,
            namespace="demo",
            entity_name="other-pod",
            attribute="metadata.deletionTimestamp",
            value="2026-07-16T01:00:00Z",
            evidence_ref="k8s:deletion-other",
        )
        other_finalizers = _fact(
            entity_id=other_entity,
            namespace="demo",
            entity_name="other-pod",
            attribute="metadata.finalizers",
            value=["aiops.example/hold"],
            evidence_ref="k8s:finalizers-other",
        )
        support_records = [other_deletion, other_finalizers]
        ledgers = [
            _ledger("case-current", [current_entity], [current_status]),
            _ledger(
                "case-other",
                [other_entity],
                [other_deletion, other_finalizers],
            ),
        ]
        hypotheses = [
            {
                "hypothesis_id": "hyp-current",
                "entity_id": current_entity,
                "summary": "当前 Pod 处于 Terminating",
                "supporting_fact_ids": [current_status["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.8,
            },
            {
                "hypothesis_id": "hyp-other",
                "entity_id": other_entity,
                "summary": "另一个 Pod 存在 finalizers",
                "supporting_fact_ids": [
                    other_deletion["fact_id"],
                    other_finalizers["fact_id"],
                ],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.9,
            },
        ]
    elif case == "stale_uid":
        target_entity = "k8s.pod:demo/terminating-stuck:uid-stale"
    elif case == "missing_finalizer":
        status = _fact(
            entity_id=current_entity,
            namespace="demo",
            entity_name="terminating-stuck",
            attribute="status.phase",
            value="Terminating",
            evidence_ref="k8s:status-current",
        )
        support_records = [current_deletion, status]
    elif case == "empty_finalizer":
        empty_finalizers = _fact(
            entity_id=current_entity,
            namespace="demo",
            entity_name="terminating-stuck",
            attribute="metadata.finalizers",
            value=[],
            evidence_ref="k8s:finalizers-empty",
        )
        support_records = [current_deletion, empty_finalizers]
    elif case == "empty_finalizer_text":
        empty_finalizers = _fact(
            entity_id=current_entity,
            namespace="demo",
            entity_name="terminating-stuck",
            attribute="metadata.finalizers",
            value="<none>",
            evidence_ref="k8s:finalizers-empty-text",
        )
        support_records = [current_deletion, empty_finalizers]
    elif case == "runbook_only":
        runbook_deletion = _fact(
            entity_id=current_entity,
            namespace="demo",
            entity_name="terminating-stuck",
            attribute="metadata.deletionTimestamp",
            value="2026-07-16T01:00:00Z",
            evidence_ref="runbook:deletion",
            source_system="runbook",
        )
        runbook_finalizers = _fact(
            entity_id=current_entity,
            namespace="demo",
            entity_name="terminating-stuck",
            attribute="metadata.finalizers",
            value=["aiops.example/hold"],
            evidence_ref="runbook:finalizers",
            source_system="runbook",
        )
        support_records = [runbook_deletion, runbook_finalizers]

    support_ids = [record["fact_id"] for record in support_records]
    if not ledgers:
        ledgers = [
            _ledger("case-current", [current_entity], support_records)
        ]
    if not hypotheses:
        hypotheses = [
            {
                "hypothesis_id": "hyp-current",
                "entity_id": current_entity,
                "summary": "模型提出 finalizer 根因候选",
                "supporting_fact_ids": support_ids,
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.9,
            }
        ]
    claim_support_ids = [
        fact_id
        for hypothesis in hypotheses
        for fact_id in hypothesis["supporting_fact_ids"]
    ]
    plan_data = _finalizer_plan(
        entity_id=target_entity,
        namespace="demo",
        pod="terminating-stuck",
        supporting_fact_ids=support_ids,
    )
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="模型提出 finalizer 根因候选",
        hypotheses=hypotheses,
        supporting_fact_ids=claim_support_ids,
    )
    extra_tool_data = (
        [{"tool": "fetch_runbook", "data": "deletionTimestamp 与 finalizers 非空"}]
        if case == "runbook_only"
        else None
    )
    node = _node_with_response(_report_with_remediation_plan(plan_data))

    conclusion = node.execute(
        {
            "question": "为什么 Pod 一直 Terminating？",
            "layer": Layer.L1,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                *ledgers,
                extra_tool_data=extra_tool_data,
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]
    plan = extract_remediation_plan(conclusion)

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.actions == []
    assert all(group.get("auto_fixable") is False for group in plan.issue_groups)


@pytest.mark.parametrize("resource_form", ["pod", "pods", "pod/name"])
def test_fact_ledger_diagnostic_only_rejects_finalizer_target_aliases(
    resource_form,
):
    entity_id = "k8s.pod:demo/terminating-stuck:uid-current"
    deletion = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="terminating-stuck",
        attribute="metadata.deletionTimestamp",
        value="2026-07-16T01:00:00Z",
        evidence_ref="k8s:deletion-current",
    )
    finalizers = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="terminating-stuck",
        attribute="metadata.finalizers",
        value=["aiops.example/hold"],
        evidence_ref="k8s:finalizers-current",
    )
    support_ids = [deletion["fact_id"], finalizers["fact_id"]]
    plan_data = _finalizer_plan(
        entity_id=entity_id,
        namespace="demo",
        pod="terminating-stuck",
        supporting_fact_ids=support_ids,
        resource_form=resource_form,
    )

    plan = _execute_fact_bound_plan(
        plan_data=plan_data,
        entity_id=entity_id,
        records=[deletion, finalizers],
        layer=Layer.L1,
    )

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.fix_type == "manual_only"
    assert plan.requires_human_approval is True
    assert plan.actions == []


@pytest.mark.parametrize("resource_form", ["pod", "pods", "pod/name"])
@pytest.mark.parametrize(
    "evidence_case",
    [
        "missing_deletion",
        "missing_finalizers",
        "empty_finalizers",
        "stale_uid",
    ],
)
def test_fact_bound_finalizer_alias_rejects_invalid_entity_facts(
    resource_form,
    evidence_case,
):
    entity_id = "k8s.pod:demo/terminating-stuck:uid-current"
    target_entity_id = entity_id
    deletion = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="terminating-stuck",
        attribute="metadata.deletionTimestamp",
        value="2026-07-16T01:00:00Z",
        evidence_ref="k8s:deletion-current",
    )
    finalizers = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="terminating-stuck",
        attribute="metadata.finalizers",
        value=["aiops.example/hold"],
        evidence_ref="k8s:finalizers-current",
    )
    status = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="terminating-stuck",
        attribute="status.phase",
        value="Deleting",
        evidence_ref="k8s:status-current",
    )
    empty_finalizers = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="terminating-stuck",
        attribute="metadata.finalizers",
        value=[],
        evidence_ref="k8s:finalizers-empty",
    )
    if evidence_case == "missing_deletion":
        records = [finalizers, status]
    elif evidence_case == "missing_finalizers":
        records = [deletion, status]
    elif evidence_case == "empty_finalizers":
        records = [deletion, empty_finalizers]
    else:
        records = [deletion, finalizers]
        target_entity_id = "k8s.pod:demo/terminating-stuck:uid-stale"

    support_ids = [record["fact_id"] for record in records]
    plan_data = _finalizer_plan(
        entity_id=target_entity_id,
        namespace="demo",
        pod="terminating-stuck",
        supporting_fact_ids=support_ids,
        resource_form=resource_form,
    )

    plan = _execute_fact_bound_plan(
        plan_data=plan_data,
        entity_id=entity_id,
        records=records,
        layer=Layer.L1,
    )

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.actions == []


@pytest.mark.parametrize("evidence_kind", ["runbook", "topology_only"])
def test_fact_bound_generic_action_rejects_non_environment_authorization(
    evidence_kind,
):
    entity_id = "k8s.deployment:demo/api:uid-deployment"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        entity_kind="Deployment",
        dimension="topology" if evidence_kind == "topology_only" else "logging",
        fact_type="relationship" if evidence_kind == "topology_only" else "log",
        attribute=(
            "topology.relationship"
            if evidence_kind == "topology_only"
            else "runbook.advice"
        ),
        value=(
            {
                "relationship": "owned_by",
                "source_entity_id": "k8s.pod:demo/api-pod:uid-pod",
                "target_entity_id": entity_id,
            }
            if evidence_kind == "topology_only"
            else {"message": "patch replicas to recover"}
        ),
        source_system="topology" if evidence_kind == "topology_only" else "runbook",
        evidence_ref=f"{evidence_kind}:deployment-api",
    )
    plan_data = _deployment_patch_plan(
        entity_id=entity_id,
        supporting_fact_ids=[fact["fact_id"]],
    )
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="模型提出通用工作负载根因候选",
        hypotheses=[
            {
                "hypothesis_id": "hyp-deployment",
                "entity_id": entity_id,
                "summary": "通用工作负载根因候选",
                "supporting_fact_ids": [fact["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.9,
            }
        ],
        supporting_fact_ids=[fact["fact_id"]],
    )
    node = _node_with_response(_report_with_remediation_plan(plan_data))

    conclusion = node.execute(
        {
            "question": "为什么工作负载异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-deployment", [entity_id], [fact])
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]
    plan = extract_remediation_plan(conclusion)

    assert plan is not None
    assert plan.remediation_available is False


def test_rejected_non_pod_ledger_still_forces_diagnostic_only_remediation():
    entity_id = "k8s.deployment:demo/api:uid-deployment"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        entity_kind="Deployment",
        dimension="configuration",
        fact_type="configuration",
        attribute="spec.replicas",
        value=2,
        source_system="kubernetes",
        evidence_ref="k8s:deployment-api",
    )
    plan_data = _deployment_patch_plan(
        entity_id=entity_id,
        supporting_fact_ids=[fact["fact_id"]],
    )
    node = _node_with_response(_report_with_remediation_plan(plan_data))

    conclusion = node.execute(
        {
            "question": "为什么工作负载异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-rejected-deployment", [entity_id], [fact])
            ),
            "rca_analysis": _rca_claim(
                diagnostic_status="diagnosed",
                root_cause_summary="模型提出工作负载根因候选",
                hypotheses=[
                    {
                        "hypothesis_id": "hyp-rejected-deployment",
                        "entity_id": entity_id,
                        "summary": "模型提出工作负载根因候选",
                        "supporting_fact_ids": [fact["fact_id"]],
                        "contradicting_fact_ids": [],
                        "unknowns": [],
                        "confidence": 0.9,
                    }
                ],
                supporting_fact_ids=[fact["fact_id"]],
            ),
            "thinking_events": [],
        }
    )["conclusion"]
    plan = extract_remediation_plan(conclusion)

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.fix_type == "manual_only"
    assert plan.requires_human_approval is True
    assert plan.actions == []
    assert "kubectl patch deployment" not in conclusion
    assert plan.actions == []


@pytest.mark.parametrize(
    "source_system",
    [
        "llm",
        "assistant",
        "generated",
        "model-generated",
        "documentation",
        "documentation-cache",
        "reference",
        "reference-material",
        "unrecognized-observer",
        "elasticsearch+unknown",
        "kubernetes+llm",
        "prometheus+assistant",
        "tempo+generated",
        "logs+documentation",
        "deepflow+reference",
        "kubernetes+runbook",
        "kubernetes+topology",
    ],
)
def test_fact_bound_generic_action_rejects_untrusted_source_systems(
    source_system,
):
    entity_id = "k8s.deployment:demo/api:uid-deployment"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        entity_kind="Deployment",
        dimension="logging",
        fact_type="log",
        attribute="observation.message",
        value={"message": "same-entity observation"},
        source_system=source_system,
        evidence_ref=f"{source_system}:deployment-api",
    )
    plan_data = _deployment_patch_plan(
        entity_id=entity_id,
        supporting_fact_ids=[fact["fact_id"]],
    )
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="same-entity candidate",
        hypotheses=[
            {
                "hypothesis_id": "hyp-deployment",
                "entity_id": entity_id,
                "summary": "same-entity candidate",
                "supporting_fact_ids": [fact["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.9,
            }
        ],
        supporting_fact_ids=[fact["fact_id"]],
    )
    node = _node_with_response(_report_with_remediation_plan(plan_data))

    conclusion = node.execute(
        {
            "question": "为什么工作负载异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-deployment", [entity_id], [fact])
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]
    plan = extract_remediation_plan(conclusion)

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.actions == []


@pytest.mark.parametrize(
    "source_system",
    [
        "kubernetes++prometheus",
        "+kubernetes",
        "kubernetes+",
    ],
)
def test_fact_bound_generic_action_rejects_malformed_composite_source_system(
    source_system,
):
    entity_id = "k8s.deployment:demo/api:uid-deployment"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        entity_kind="Deployment",
        dimension="logging",
        fact_type="log",
        attribute="observation.message",
        value={"message": "same-entity observation"},
        source_system=source_system,
        evidence_ref=f"{source_system}:deployment-api",
    )
    plan_data = _deployment_patch_plan(
        entity_id=entity_id,
        supporting_fact_ids=[fact["fact_id"]],
    )
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="same-entity candidate",
        hypotheses=[
            {
                "hypothesis_id": "hyp-deployment",
                "entity_id": entity_id,
                "summary": "same-entity candidate",
                "supporting_fact_ids": [fact["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.9,
            }
        ],
        supporting_fact_ids=[fact["fact_id"]],
    )
    node = _node_with_response(_report_with_remediation_plan(plan_data))

    conclusion = node.execute(
        {
            "question": "为什么工作负载异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-deployment", [entity_id], [fact])
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]
    plan = extract_remediation_plan(conclusion)

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.actions == []


@pytest.mark.parametrize(
    "source_system",
    [
        "elasticsearch+kubernetes",
        "deepflow+kubernetes",
    ],
)
def test_fact_ledger_diagnostic_only_rejects_trusted_composite_source_system(
    source_system,
):
    entity_id = "k8s.deployment:demo/api:uid-deployment"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        entity_kind="Deployment",
        dimension="kubernetes",
        fact_type="state",
        attribute="spec.replicas",
        value=2,
        source_system=source_system,
        evidence_ref="merged:deployment-api",
    )
    plan_data = _deployment_patch_plan(
        entity_id=entity_id,
        supporting_fact_ids=[fact["fact_id"]],
    )
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="same-entity candidate",
        hypotheses=[
            {
                "hypothesis_id": "hyp-deployment",
                "entity_id": entity_id,
                "summary": "same-entity candidate",
                "supporting_fact_ids": [fact["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.9,
            }
        ],
        supporting_fact_ids=[fact["fact_id"]],
    )
    node = _node_with_response(_report_with_remediation_plan(plan_data))

    conclusion = node.execute(
        {
            "question": "为什么工作负载异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-deployment", [entity_id], [fact])
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]
    plan = extract_remediation_plan(conclusion)

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.fix_type == "manual_only"
    assert plan.requires_human_approval is True
    assert plan.actions == []


@pytest.mark.parametrize(
    "verify_command",
    [
        "kubectl rollout status pod/api -n demo --timeout=60s",
        "kubectl rollout status deployment/api -n other --timeout=60s",
        "kubectl rollout status deployment/other -n demo --timeout=60s",
    ],
)
def test_fact_bound_action_rejects_verify_command_target_mismatch(
    verify_command,
):
    entity_id = "k8s.deployment:demo/api:uid-deployment"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        entity_kind="Deployment",
        dimension="logging",
        fact_type="log",
        attribute="observation.message",
        value={"message": "same-entity observation"},
        source_system="kubernetes",
        evidence_ref="kubernetes:deployment-api",
    )
    plan_data = _deployment_patch_plan(
        entity_id=entity_id,
        supporting_fact_ids=[fact["fact_id"]],
    )
    plan_data["actions"][0]["verify_command"] = verify_command
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="same-entity candidate",
        hypotheses=[
            {
                "hypothesis_id": "hyp-deployment",
                "entity_id": entity_id,
                "summary": "same-entity candidate",
                "supporting_fact_ids": [fact["fact_id"]],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.9,
            }
        ],
        supporting_fact_ids=[fact["fact_id"]],
    )
    node = _node_with_response(_report_with_remediation_plan(plan_data))

    conclusion = node.execute(
        {
            "question": "为什么工作负载异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(
                _ledger("case-deployment", [entity_id], [fact])
            ),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]
    plan = extract_remediation_plan(conclusion)

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.actions == []


@pytest.mark.parametrize(
    ("command_field", "command"),
    [
        (
            "dry_run_command",
            "kubectl get deployment api other -n demo",
        ),
        (
            "execute_command",
            "kubectl delete deployment api other -n demo",
        ),
        (
            "verify_command",
            "kubectl get deployment api other -n demo",
        ),
        (
            "dry_run_command",
            "kubectl get deployment/api deployment/other -n demo",
        ),
        (
            "execute_command",
            "kubectl delete deployment/api deployment/other -n demo",
        ),
        (
            "verify_command",
            "kubectl get deployment/api deployment/other -n demo",
        ),
    ],
)
def test_fact_bound_action_rejects_multi_target_commands(
    command_field,
    command,
):
    entity_id = "k8s.deployment:demo/api:uid-deployment"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        entity_kind="Deployment",
        dimension="logging",
        fact_type="log",
        attribute="observation.message",
        value={"message": "same-entity observation"},
        source_system="kubernetes",
        evidence_ref="kubernetes:deployment-api",
    )
    plan_data = _deployment_patch_plan(
        entity_id=entity_id,
        supporting_fact_ids=[fact["fact_id"]],
    )
    plan_data["actions"][0][command_field] = command

    plan = _execute_fact_bound_plan(
        plan_data=plan_data,
        entity_id=entity_id,
        records=[fact],
    )

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.actions == []


def test_inconclusive_claim_with_valid_same_entity_facts_authorizes_no_action():
    entity_id = "k8s.deployment:demo/api:uid-deployment"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        entity_kind="Deployment",
        dimension="kubernetes",
        fact_type="state",
        attribute="spec.replicas",
        value=2,
        source_system="kubernetes",
        evidence_ref="kubernetes:deployment-api-replicas",
    )
    plan_data = _deployment_patch_plan(
        entity_id=entity_id,
        supporting_fact_ids=[fact["fact_id"]],
    )

    plan = _execute_fact_bound_plan(
        plan_data=plan_data,
        entity_id=entity_id,
        records=[fact],
        diagnostic_status="inconclusive",
    )

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.actions == []


def test_invalid_claim_with_rejected_non_pod_ledger_authorizes_no_action():
    entity_id = "k8s.deployment:demo/api:uid-deployment"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        entity_kind="Deployment",
        dimension="kubernetes",
        fact_type="state",
        attribute="spec.replicas",
        value=2,
        source_system="kubernetes",
        evidence_ref="kubernetes:deployment-api-replicas",
    )
    invalid_fact_id = "fact-unknown000000"
    plan_data = _deployment_patch_plan(
        entity_id=entity_id,
        supporting_fact_ids=[fact["fact_id"]],
    )
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="same-entity candidate",
        hypotheses=[
            {
                "hypothesis_id": "hyp-invalid-claim",
                "entity_id": entity_id,
                "summary": "same-entity candidate",
                "supporting_fact_ids": [fact["fact_id"], invalid_fact_id],
                "contradicting_fact_ids": [],
                "unknowns": [],
                "confidence": 0.9,
            }
        ],
        supporting_fact_ids=[fact["fact_id"], invalid_fact_id],
    )
    evidence = _fact_evidence(
        _ledger("case-invalid-claim", [entity_id], [fact])
    )
    node = _node_with_response(_report_with_remediation_plan(plan_data))
    context = node._build_fact_report_context(
        evidence_analysis=evidence,
        rca_analysis=claim,
    )

    assert context is None

    conclusion = node.execute(
        {
            "question": "为什么工作负载异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": evidence,
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]
    plan = extract_remediation_plan(conclusion)

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.actions == []


@pytest.mark.parametrize(
    ("family", "execute_command", "_attribute", "_value"),
    _ACTION_SPECIFIC_FACT_CASES,
)
def test_unrelated_same_entity_fact_cannot_authorize_write_family(
    family,
    execute_command,
    _attribute,
    _value,
):
    entity_id = "k8s.deployment:demo/api:uid-deployment"
    unrelated_fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        entity_kind="Deployment",
        dimension="logging",
        fact_type="log",
        attribute="observation.message",
        value={"message": "same-entity but unrelated observation"},
        source_system="elasticsearch",
        evidence_ref=f"logging:unrelated-{family}",
    )
    plan_data = _deployment_patch_plan(
        entity_id=entity_id,
        supporting_fact_ids=[unrelated_fact["fact_id"]],
    )
    plan_data["actions"][0]["execute_command"] = execute_command

    plan = _execute_fact_bound_plan(
        plan_data=plan_data,
        entity_id=entity_id,
        records=[unrelated_fact],
    )

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.actions == []


@pytest.mark.parametrize(
    ("family", "execute_command", "attribute", "value"),
    _ACTION_SPECIFIC_FACT_CASES,
)
def test_fact_ledger_diagnostic_only_rejects_every_matching_write_family(
    family,
    execute_command,
    attribute,
    value,
):
    entity_id = "k8s.deployment:demo/api:uid-deployment"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        entity_kind="Deployment",
        dimension="kubernetes",
        fact_type="state",
        attribute=attribute,
        value=value,
        source_system="kubernetes",
        evidence_ref=f"kubernetes:{family}-semantics",
    )
    plan_data = _deployment_patch_plan(
        entity_id=entity_id,
        supporting_fact_ids=[fact["fact_id"]],
    )
    plan_data["actions"][0]["execute_command"] = execute_command

    plan = _execute_fact_bound_plan(
        plan_data=plan_data,
        entity_id=entity_id,
        records=[fact],
    )

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.fix_type == "manual_only"
    assert plan.requires_human_approval is True
    assert plan.actions == []


@pytest.mark.parametrize(
    ("execute_command", "containers"),
    [
        (
            (
                "kubectl set image deployment/api "
                "api=registry.example/sidecar:v2 -n demo"
            ),
            [
                {
                    "name": "api",
                    "image": "registry.example/api:v1",
                },
                {
                    "name": "sidecar",
                    "image": "registry.example/sidecar:v2",
                },
            ],
        ),
        (
            (
                "kubectl set resources deployment/api -n demo "
                "--limits=memory=128Mi"
            ),
            [
                {
                    "name": "api",
                    "resources": {"limits": {"memory": "64Mi"}},
                },
                {
                    "name": "sidecar",
                    "resources": {"limits": {"memory": "128Mi"}},
                },
            ],
        ),
        (
            (
                "kubectl set env deployment/api FEATURE_FLAG=enabled "
                "--containers=api -n demo"
            ),
            [
                {
                    "name": "api",
                    "env": [{"name": "FEATURE_FLAG", "value": "disabled"}],
                },
                {
                    "name": "sidecar",
                    "env": [{"name": "FEATURE_FLAG", "value": "enabled"}],
                },
            ],
        ),
        (
            (
                "kubectl set env deployment/api FEATURE_FLAG=enabled "
                "-n demo"
            ),
            [
                {
                    "name": "api",
                    "env": [{"name": "FEATURE_FLAG", "value": "disabled"}],
                },
                {
                    "name": "sidecar",
                    "env": [{"name": "FEATURE_FLAG", "value": "enabled"}],
                },
            ],
        ),
    ],
)
def test_fact_bound_structured_container_binding_rejects_cross_scope_reuse(
    execute_command,
    containers,
):
    entity_id = "k8s.deployment:demo/api:uid-deployment"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        entity_kind="Deployment",
        attribute="spec.template.spec.containers",
        value=containers,
        evidence_ref="kubernetes:deployment-api-containers",
    )
    plan_data = _deployment_patch_plan(
        entity_id=entity_id,
        supporting_fact_ids=[fact["fact_id"]],
    )
    plan_data["actions"][0]["execute_command"] = execute_command

    plan = _execute_fact_bound_plan(
        plan_data=plan_data,
        entity_id=entity_id,
        records=[fact],
    )

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.actions == []


@pytest.mark.parametrize(
    ("execute_command", "containers"),
    [
        (
            (
                "kubectl set image deployment/api "
                "api=registry.example/api:v2 -n demo"
            ),
            [
                {
                    "name": "api",
                    "image": "registry.example/api:v2",
                },
                {
                    "name": "sidecar",
                    "image": "registry.example/sidecar:v1",
                },
            ],
        ),
        (
            (
                "kubectl set resources deployment/api -n demo "
                "--containers=api --limits=memory=128Mi"
            ),
            [
                {
                    "name": "api",
                    "resources": {"limits": {"memory": "128Mi"}},
                },
                {
                    "name": "sidecar",
                    "resources": {"limits": {"memory": "64Mi"}},
                },
            ],
        ),
        (
            (
                "kubectl set env deployment/api FEATURE_FLAG=enabled "
                "--containers=api -n demo"
            ),
            [
                {
                    "name": "api",
                    "env": [{"name": "FEATURE_FLAG", "value": "enabled"}],
                },
                {
                    "name": "sidecar",
                    "env": [{"name": "FEATURE_FLAG", "value": "disabled"}],
                },
            ],
        ),
        (
            (
                "kubectl set resources deployment/api -n demo "
                "--limits=memory=128Mi"
            ),
            [
                {
                    "name": "api",
                    "resources": {"limits": {"memory": "128Mi"}},
                },
                {
                    "name": "sidecar",
                    "resources": {"limits": {"memory": "128Mi"}},
                },
            ],
        ),
        (
            (
                "kubectl set env deployment/api FEATURE_FLAG=enabled "
                "-n demo"
            ),
            [
                {
                    "name": "api",
                    "env": [{"name": "FEATURE_FLAG", "value": "enabled"}],
                },
                {
                    "name": "sidecar",
                    "env": [{"name": "FEATURE_FLAG", "value": "enabled"}],
                },
            ],
        ),
    ],
)
def test_fact_ledger_diagnostic_only_rejects_exact_container_scope(
    execute_command,
    containers,
):
    entity_id = "k8s.deployment:demo/api:uid-deployment"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        entity_kind="Deployment",
        attribute="spec.template.spec.containers",
        value=containers,
        evidence_ref="kubernetes:deployment-api-containers",
    )
    plan_data = _deployment_patch_plan(
        entity_id=entity_id,
        supporting_fact_ids=[fact["fact_id"]],
    )
    plan_data["actions"][0]["execute_command"] = execute_command

    plan = _execute_fact_bound_plan(
        plan_data=plan_data,
        entity_id=entity_id,
        records=[fact],
    )

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.fix_type == "manual_only"
    assert plan.requires_human_approval is True
    assert plan.actions == []


@pytest.mark.parametrize(
    "operation",
    [
        {"op": "remove", "path": "/spec/replicas", "value": 2},
        {
            "op": "move",
            "from": "/status/replicas",
            "path": "/spec/replicas",
            "value": 2,
        },
        {
            "op": "copy",
            "from": "/status/replicas",
            "path": "/spec/replicas",
            "value": 2,
        },
    ],
)
def test_fact_bound_patch_operation_rejects_non_value_mutations(operation):
    entity_id = "k8s.deployment:demo/api:uid-deployment"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        entity_kind="Deployment",
        attribute="spec.replicas",
        value=2,
        evidence_ref="kubernetes:deployment-api-replicas",
    )
    plan_data = _deployment_patch_plan(
        entity_id=entity_id,
        supporting_fact_ids=[fact["fact_id"]],
    )
    patch = json.dumps([operation], separators=(",", ":"))
    plan_data["actions"][0]["execute_command"] = (
        "kubectl patch deployment api -n demo --type=json "
        f"-p '{patch}'"
    )

    plan = _execute_fact_bound_plan(
        plan_data=plan_data,
        entity_id=entity_id,
        records=[fact],
    )

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.actions == []


@pytest.mark.parametrize(
    "execute_command",
    [
        (
            "kubectl patch pod terminating-stuck -n demo --type=merge "
            "-p '{\"metadata\":{\"finalizers\":[\"attacker.example/keep\"]}}'"
        ),
        (
            "kubectl patch pod terminating-stuck -n demo --type=json "
            "-p '[{\"op\":\"add\",\"path\":\"/metadata/finalizers/-\","
            "\"value\":\"attacker.example/keep\"}]'"
        ),
        (
            "kubectl patch pod terminating-stuck -n demo --type=json "
            "-p '[{\"op\":\"remove\","
            "\"path\":\"/metadata/finalizersBackup\"}]'"
        ),
    ],
)
def test_fact_bound_finalizer_patch_shape_rejects_non_removal(
    execute_command,
):
    entity_id = "k8s.pod:demo/terminating-stuck:uid-current"
    deletion = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="terminating-stuck",
        attribute="metadata.deletionTimestamp",
        value="2026-07-16T01:00:00Z",
        evidence_ref="kubernetes:deletion-current",
    )
    finalizers = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="terminating-stuck",
        attribute="metadata.finalizers",
        value=["aiops.example/hold"],
        evidence_ref="kubernetes:finalizers-current",
    )
    records = [deletion, finalizers]
    plan_data = _finalizer_plan(
        entity_id=entity_id,
        namespace="demo",
        pod="terminating-stuck",
        supporting_fact_ids=[record["fact_id"] for record in records],
    )
    plan_data["actions"][0]["execute_command"] = execute_command

    plan = _execute_fact_bound_plan(
        plan_data=plan_data,
        entity_id=entity_id,
        records=records,
        layer=Layer.L1,
    )

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.actions == []


@pytest.mark.parametrize(
    "execute_command",
    [
        (
            "kubectl patch pod terminating-stuck -n demo --type=merge "
            "-p '{\"metadata\":{\"finalizers\":null}}'"
        ),
        (
            "kubectl patch pod terminating-stuck -n demo --type=merge "
            "-p '{\"metadata\":{\"finalizers\":[]}}'"
        ),
        (
            "kubectl patch pod terminating-stuck -n demo --type=strategic "
            "-p '{\"metadata\":{\"finalizers\":null}}'"
        ),
        (
            "kubectl patch pod terminating-stuck -n demo --type=strategic "
            "-p '{\"metadata\":{\"finalizers\":[]}}'"
        ),
        (
            "kubectl patch pod terminating-stuck -n demo --type=json "
            "-p '[{\"op\":\"remove\",\"path\":\"/metadata/finalizers\"}]'"
        ),
    ],
)
def test_fact_ledger_diagnostic_only_rejects_actual_finalizer_removal(
    execute_command,
):
    entity_id = "k8s.pod:demo/terminating-stuck:uid-current"
    deletion = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="terminating-stuck",
        attribute="metadata.deletionTimestamp",
        value="2026-07-16T01:00:00Z",
        evidence_ref="kubernetes:deletion-current",
    )
    finalizers = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="terminating-stuck",
        attribute="metadata.finalizers",
        value=["aiops.example/hold"],
        evidence_ref="kubernetes:finalizers-current",
    )
    records = [deletion, finalizers]
    plan_data = _finalizer_plan(
        entity_id=entity_id,
        namespace="demo",
        pod="terminating-stuck",
        supporting_fact_ids=[record["fact_id"] for record in records],
    )
    plan_data["actions"][0]["execute_command"] = execute_command

    plan = _execute_fact_bound_plan(
        plan_data=plan_data,
        entity_id=entity_id,
        records=records,
        layer=Layer.L1,
    )

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.fix_type == "manual_only"
    assert plan.requires_human_approval is True
    assert plan.actions == []


@pytest.mark.parametrize(
    "command_field",
    [
        "dry_run_command",
        "execute_command",
        "verify_command",
    ],
)
@pytest.mark.parametrize(
    "option_suffix",
    [
        "--mystery=value",
        "--mystery value",
        "-x=value",
        "-xvalue",
        "-x value",
        "-l app=api",
        "-l=app=api",
        "--selector=app=api",
        "--selector app=api",
        "--field-selector=metadata.name=api",
        "--field-selector metadata.name=api",
        "-f /tmp/probe.yaml",
        "-f=/tmp/probe.yaml",
        "--filename=/tmp/probe.yaml",
        "--filename /tmp/probe.yaml",
        "--all",
        "-A",
        "--all-namespaces",
    ],
)
def test_fact_bound_action_rejects_ambiguous_option_boundaries(
    command_field,
    option_suffix,
):
    entity_id = "k8s.deployment:demo/api:uid-deployment"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        entity_kind="Deployment",
        dimension="logging",
        fact_type="log",
        attribute="observation.message",
        value={"message": "same-entity observation"},
        source_system="kubernetes",
        evidence_ref="kubernetes:deployment-api",
    )
    plan_data = _deployment_patch_plan(
        entity_id=entity_id,
        supporting_fact_ids=[fact["fact_id"]],
    )
    verb = "delete" if command_field == "execute_command" else "get"
    plan_data["actions"][0][command_field] = (
        f"kubectl {verb} deployment api -n demo {option_suffix}"
    )

    plan = _execute_fact_bound_plan(
        plan_data=plan_data,
        entity_id=entity_id,
        records=[fact],
    )

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.actions == []


@pytest.mark.parametrize(
    ("command_field", "command", "attribute", "value"),
    [
        (
            "dry_run_command",
            "kubectl get deployment api --namespace=demo --output=yaml",
            "spec.replicas",
            2,
        ),
        (
            "dry_run_command",
            "kubectl patch deployment api -n demo "
            "-p '{\"spec\":{\"replicas\":2}}' --type=merge "
            "--dry-run=client -o yaml",
            "spec.replicas",
            2,
        ),
        (
            "execute_command",
            "kubectl patch deployment api -n=demo "
            "--patch '{\"spec\":{\"replicas\":2}}' --type merge",
            "spec.replicas",
            2,
        ),
        (
            "execute_command",
            "kubectl delete deployment api -n demo "
            "--grace-period=0 --wait=false",
            "lifecycle.desired_state",
            "absent",
        ),
        (
            "execute_command",
            "kubectl scale deployment api -n demo --replicas=2",
            "spec.replicas",
            2,
        ),
        (
            "execute_command",
            "kubectl set resources deployment api -n demo "
            "--containers=api --limits=memory=128Mi "
            "--requests=memory=64Mi",
            "spec.template.spec.containers",
            [
                {
                    "name": "api",
                    "resources": {
                        "limits": {"memory": "128Mi"},
                        "requests": {"memory": "64Mi"},
                    },
                }
            ],
        ),
        (
            "execute_command",
            "kubectl set image deployment/api api=example.invalid/api:v2 "
            "-n demo",
            "spec.template.spec.containers",
            {
                "name": "api",
                "image": "example.invalid/api:v2",
            },
        ),
        (
            "verify_command",
            "kubectl rollout status deployment/api -n demo --timeout=60s",
            "spec.replicas",
            2,
        ),
        (
            "verify_command",
            "kubectl get deployment api -n demo "
            "--ignore-not-found --watch=false",
            "spec.replicas",
            2,
        ),
        (
            "verify_command",
            "kubectl logs deployment/api -n demo "
            "--container=api --since=5m --tail=100",
            "spec.replicas",
            2,
        ),
    ],
)
def test_fact_ledger_diagnostic_only_rejects_known_single_object_options(
    command_field,
    command,
    attribute,
    value,
):
    entity_id = "k8s.deployment:demo/api:uid-deployment"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        entity_kind="Deployment",
        dimension="kubernetes",
        fact_type="state",
        attribute=attribute,
        value=value,
        source_system="kubernetes",
        evidence_ref="kubernetes:deployment-api",
    )
    plan_data = _deployment_patch_plan(
        entity_id=entity_id,
        supporting_fact_ids=[fact["fact_id"]],
    )
    plan_data["actions"][0][command_field] = command

    plan = _execute_fact_bound_plan(
        plan_data=plan_data,
        entity_id=entity_id,
        records=[fact],
    )

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.fix_type == "manual_only"
    assert plan.requires_human_approval is True
    assert plan.actions == []


def test_remediation_prompt_marks_fact_ledger_as_diagnostic_only():
    prompt = FACT_LEDGER_REMEDIATION_PLAN_PROMPT
    assert "Fact Ledger 主路径仅用于诊断" in prompt
    assert '"fix_type": "manual_only"' in prompt
    assert '"actions": []' in prompt
    assert "Remediation Policy Contract" in prompt
    assert "get、describe、logs、top、rollout status" in prompt
    assert "supporting_fact_ids" not in prompt
    assert "target_entity_id" not in prompt
    assert '"remediation_available": true' not in prompt


def test_t017_authoritative_report_rebuilds_exact_sections_from_validated_facts_only():
    entity_id = "k8s.pod:demo/api:uid-api"
    metric = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        dimension="metrics",
        fact_type="measurement",
        attribute="request_latency_seconds",
        value={"value": 0.42},
        unit="s",
        source_system="prometheus",
        evidence_ref="prometheus:latency:1",
        timestamp="2026-07-30T00:00:00Z",
    )
    log = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        dimension="logging",
        fact_type="log",
        attribute="log.message",
        value={"message": "validated source log line"},
        source_system="elasticsearch",
        evidence_ref="logs:api:1",
        timestamp="2026-07-30T00:00:01Z",
    )
    span = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        dimension="tracing",
        fact_type="span",
        attribute="application_span",
        value={
            "trace_id": "0123456789abcdef0123456789abcdef",
            "status_code": 200,
        },
        source_system="tempo",
        evidence_ref="tempo:span:1",
    )
    topology = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        dimension="topology",
        fact_type="relationship",
        attribute="topology.relationship",
        value={
            "source": {"entity_id": entity_id, "kind": "Pod"},
            "relation": "calls",
            "target": {
                "entity_id": "k8s.service:demo/backend:uid-b",
                "kind": "Service",
            },
        },
        source_system="kubernetes",
        evidence_ref="topology:edge:1",
    )
    partial = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        dimension="coverage",
        fact_type="coverage",
        attribute="coverage.logging",
        value={"dimension": "logging", "coverage": "partial"},
        source_system="elasticsearch",
        evidence_ref="coverage:logging",
        directness="derived",
        confidence="weak",
        strength="context",
    )
    partial["evidence_refs"] = []
    partial["fact_id"] = _canonical_fact_id(partial)
    ledger = FactLedger.model_validate(
        _ledger(
            "case-t017-authoritative-report",
            [entity_id],
            [metric, log, span, topology, partial],
        )
    )
    supporting_ids = [
        metric["fact_id"],
        log["fact_id"],
        span["fact_id"],
        topology["fact_id"],
    ]
    validated_claim = {
        "diagnostic_status": "diagnosed",
        "confidence": 0.9,
        "hypotheses": [
            {
                "hypothesis_id": "hyp-api",
                "entity_id": entity_id,
                "supporting_fact_ids": supporting_ids,
                "contradicting_fact_ids": [],
            }
        ],
        "claim_validation": {
            "valid": True,
            "valid_supporting_fact_ids": supporting_ids,
            "valid_contradicting_fact_ids": [],
            "reasons": [],
        },
    }
    malicious_model_report = """
## 诊断概览
模型声称结论已经确认。

## 现象描述
仅保留非权威说明。

## 可观测性数据

### 三大观测维度

| 维度 | 数据来源 | 覆盖状态 | 关键原始信号 | 证据 ref |
|---|---|---|---|---|
| **Metrics** | model | present | sampled threshold crossing | fake-ref |
| **Logging** | model | present | oom_score_adj=-997 | fake-ref |
| **Tracing** | model | present | service unavailable | fake-ref |
| **K8s** | model | present | unsupported | fake-ref |

### 拓扑关系（实体与边）
- model invented Database --causes--> Pod relation.

## 根因分析
- sampled threshold crossing proves service unavailable and oom_score_adj=-997.

## 修复建议
- Set a fixed target of 128Mi.
- `kubectl set resources deployment/api -n demo --limits=memory=128Mi`
""".strip()

    report = ConclusionFormatterNode._apply_fact_ledger_report_contract(
        malicious_model_report,
        ledgers=[ledger],
        validated_claim=validated_claim,
    )

    assert "validated source log line" in report
    assert "0123456789abcdef0123456789abcdef" in report
    assert "topology:edge:1" in report
    assert "sampled threshold crossing" not in report
    assert "oom_score_adj" not in report
    assert "service unavailable" not in report
    assert "Database --causes--> Pod" not in report
    assert "128Mi" not in report
    assert "kubectl set resources" not in report
    for code in (
        "sampled_interval_unknown",
        "representative_trace_only",
        "availability_unmeasured",
        "capacity_policy_missing",
        "topology_relation_only",
        "partial_coverage",
    ):
        assert code in report
    plan = extract_remediation_plan(report)
    assert plan is not None
    assert plan.remediation_available is False
    assert plan.fix_type == "manual_only"
    assert plan.requires_human_approval is True
    assert plan.actions == []


def test_t017_coverage_fact_targets_logging_before_dimension_filtering():
    entity_id = "k8s.pod:demo/api:uid-api"
    log = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        dimension="logging",
        fact_type="log",
        attribute="log.message",
        value={"message": "validated partial log"},
        source_system="elasticsearch",
        evidence_ref="logs:partial:1",
    )
    partial = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        dimension="coverage",
        fact_type="coverage",
        attribute="coverage.logging",
        value={"dimension": "logging", "coverage": "partial"},
        source_system="elasticsearch",
        evidence_ref="coverage:logging",
        directness="derived",
        confidence="weak",
        strength="context",
    )
    partial["evidence_refs"] = []
    partial["fact_id"] = _canonical_fact_id(partial)
    ledger = FactLedger.model_validate(
        _ledger("case-t017-target-coverage", [entity_id], [log, partial])
    )
    model_table = """| 维度 | 数据来源 | 覆盖状态 | 关键原始信号 | 证据 ref |
|---|---|---|---|---|
| **Logging** | model | present | invented | fake-ref |"""

    report, available_dimensions = (
        ConclusionFormatterNode._enforce_fact_ledger_observability_sections(
            model_table,
            ledgers=[ledger],
        )
    )

    assert available_dimensions == {"logging"}
    assert "| **Logging** | elasticsearch | partial |" in report
    assert "| **Logging** | model | present |" not in report


def test_t017_authoritative_report_rebuilds_adversarial_overview_and_phenomenon():
    entity_id = "k8s.pod:demo/api:uid-api"
    fact = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        dimension="logging",
        fact_type="log",
        attribute="log.message",
        value={"message": "validated phenomenon source"},
        source_system="elasticsearch",
        evidence_ref="logs:validated-phenomenon",
    )
    ledger = FactLedger.model_validate(
        _ledger("case-t017-whole-report-boundary", [entity_id], [fact])
    )
    validated_claim = {
        "diagnostic_status": "diagnosed",
        "confidence": 0.9,
        "hypotheses": [{
            "hypothesis_id": "hyp-api",
            "entity_id": entity_id,
            "supporting_fact_ids": [fact["fact_id"]],
            "contradicting_fact_ids": [],
        }],
        "claim_validation": {
            "valid": True,
            "valid_supporting_fact_ids": [fact["fact_id"]],
            "valid_contradicting_fact_ids": [],
            "reasons": [],
        },
    }
    malicious_report = """
## 诊断概览
UNSUPPORTED_EXACT=999.99 proves service unavailable at a fixed 128Mi limit.
The internal mechanism sets oom_score_adj=-997 before termination.

## 现象描述
sampled threshold crossing proves the outage.
Database --causes--> Pod is the causal topology.

## 可观测性数据
model-authored placeholder

## 根因分析
model-authored placeholder

## 修复建议
model-authored placeholder
""".strip()

    report = ConclusionFormatterNode._apply_fact_ledger_report_contract(
        malicious_report,
        ledgers=[ledger],
        validated_claim=validated_claim,
    )

    assert "validated phenomenon source" in report
    assert fact["fact_id"] in report
    for unsupported in (
        "UNSUPPORTED_EXACT=999.99",
        "service unavailable",
        "128Mi",
        "oom_score_adj",
        "sampled threshold crossing",
        "Database --causes--> Pod",
    ):
        assert unsupported not in report
    assert report.count("## 诊断概览") == 1
    assert report.count("## 现象描述") == 1


@pytest.mark.parametrize(
    ("source", "legacy_contract"),
    [
        ("mcp_canonical", False),
        ("robusta_legacy_adapter", True),
    ],
    ids=["canonical", "trusted-legacy"],
)
def test_t017_authoritative_report_allowlists_complete_report_structure(
    source,
    legacy_contract,
):
    entity_id = "k8s.pod:demo/api:uid-api"
    metric = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        dimension="metrics",
        fact_type="measurement",
        attribute="request_latency_seconds",
        value={"value": 42.125},
        unit="s",
        source_system="prometheus",
        evidence_ref="prometheus:validated-latency",
    )
    log = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        dimension="logging",
        fact_type="log",
        attribute="log.message",
        value={"message": "validated distributed evidence"},
        source_system="elasticsearch",
        evidence_ref="logs:validated-distributed",
    )
    span = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        dimension="tracing",
        fact_type="span",
        attribute="application_span",
        value={
            "trace_id": "0123456789abcdef0123456789abcdef",
            "status_code": 200,
        },
        source_system="tempo",
        evidence_ref="tempo:validated-span",
    )
    topology = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        dimension="topology",
        fact_type="relationship",
        attribute="topology.relationship",
        value={
            "source": {"entity_id": entity_id, "kind": "Pod"},
            "relation": "calls",
            "target": {
                "entity_id": "k8s.service:demo/backend:uid-b",
                "kind": "Service",
            },
        },
        source_system="deepflow",
        evidence_ref="topology:validated-edge",
    )
    partial = _fact(
        entity_id=entity_id,
        namespace="demo",
        entity_name="api",
        dimension="coverage",
        fact_type="coverage",
        attribute="coverage.logging",
        value={"dimension": "logging", "coverage": "partial"},
        source_system="elasticsearch",
        evidence_ref="coverage:logging",
        directness="derived",
        confidence="weak",
        strength="context",
    )
    partial["evidence_refs"] = []
    partial["fact_id"] = _canonical_fact_id(partial)
    records = [metric, log, span, topology, partial]
    ledger = _ledger(
        "case-t017-complete-report-allowlist",
        [entity_id],
        records,
    )
    ledger["source"] = source
    ledger["legacy_contract"] = legacy_contract
    supporting_ids = [
        record["fact_id"]
        for record in records
        if record["fact_type"] != "coverage"
    ]
    claim = _rca_claim(
        diagnostic_status="diagnosed",
        root_cause_summary="validated records only",
        hypotheses=[{
            "hypothesis_id": "hyp-complete-report-allowlist",
            "entity_id": entity_id,
            "summary": "validated records only",
            "supporting_fact_ids": supporting_ids,
            "contradicting_fact_ids": [],
            "unknowns": [],
            "confidence": 0.9,
        }],
        supporting_fact_ids=supporting_ids,
    )
    malicious_report = """
# MODEL_AUTHORED_PREAMBLE
This unrecognized preamble must not become report authority.

## 诊断概览
model placeholder

## 现象描述
model placeholder

## 证据链
UNSUPPORTED_EXACT=999.99

## 影响范围
service unavailable

## 执行过程
oom_score_adj=-997 is the internal mechanism

## 限制说明
sampled threshold crossing proves a global outage

## 模型补充
Database --causes--> Pod

## 可观测性数据
model placeholder

## 根因分析
model placeholder

## 修复建议
model placeholder
""".strip()
    node = _node_with_response(malicious_report)

    report = node.execute(
        {
            "question": "为什么 api Pod 异常？",
            "layer": Layer.L2,
            "layer_analysis": "{}",
            "evidence_analysis": _fact_evidence(ledger),
            "rca_analysis": claim,
            "thinking_events": [],
        }
    )["conclusion"]

    for unsupported in (
        "MODEL_AUTHORED_PREAMBLE",
        "UNSUPPORTED_EXACT=999.99",
        "oom_score_adj",
        "sampled threshold crossing",
        "service unavailable",
        "Database --causes--> Pod",
    ):
        assert report.count(unsupported) == 0
    for heading in (
        "## 证据链",
        "## 影响范围",
        "## 执行过程",
        "## 限制说明",
        "## 模型补充",
    ):
        assert heading not in report
    assert "42.125" in report
    assert "validated distributed evidence" in report
    for fact_id in supporting_ids:
        assert fact_id in report
    for evidence_ref in (
        "prometheus:validated-latency",
        "logs:validated-distributed",
        "tempo:validated-span",
        "topology:validated-edge",
    ):
        assert evidence_ref in report
    for code in (
        "sampled_interval_unknown",
        "representative_trace_only",
        "availability_unmeasured",
        "capacity_policy_missing",
        "topology_relation_only",
        "partial_coverage",
    ):
        assert code in report
    plan = extract_remediation_plan(report)
    assert plan is not None
    assert plan.remediation_available is False
    assert plan.fix_type == "manual_only"
    assert plan.requires_human_approval is True
    assert plan.actions == []


def test_ask_conclusion_normalizes_finalizer_patch_plan_when_actions_missing():
    report = """
## 📊 诊断概览
Pod terminating-stuck 当前仍在 Terminating，deletionTimestamp 已存在且 finalizers 非空。

## 🛠️ 修复建议
优先移除已确认阻塞的 finalizer：
```bash
kubectl patch pod terminating-stuck -n aiops-e2e -p '{"metadata":{"finalizers":null}}' --type=merge
```

## 🧩 结构化修复计划
```json
{
  "remediation_available": false,
  "fix_type": "manual_only",
  "risk_level": "medium",
  "requires_human_approval": true,
  "basis": ["deletionTimestamp exists", "finalizers: aiops.e2e/hold"],
  "actions": []
}
```
"""
    node = _node_with_response(report)

    result = node.execute(
        {
            "question": "我的集群有什么问题？",
            "layer": Layer.L1,
            "layer_analysis": '{"pod_abnormal_type":"TerminatingStuck"}',
            "evidence_analysis": _finalizer_evidence(),
            "rca_analysis": '{"root_cause":"Pod finalizer 清理卡住"}',
            "thinking_events": [],
        }
    )

    plan = extract_remediation_plan(result["conclusion"])

    assert plan is not None
    assert plan.remediation_available is True
    assert plan.fix_type == "remove_finalizer"
    assert plan.actions[0].execute_command == (
        "kubectl patch pod terminating-stuck -n aiops-e2e "
        "-p '{\"metadata\":{\"finalizers\":null}}' --type=merge"
    )
    assert plan.actions[0].verify_command == "kubectl get pod terminating-stuck -n aiops-e2e"


def test_ask_conclusion_downgrades_unsupported_oom_patch_and_unknown_secret_command():
    report = """
## 📊 诊断概览
两个 Pod 分别发生 OOMKilled 和配置缺失。

## 🎯 根因分析
- trace-oom-api 内存限制不足，当前 Limit 80Mi 无法支撑峰值 70.9Mi。
- Trace 显示 `/allocate` 操作触发 OOM。

## 🛠️ 修复建议
1. 将内存 Limit 自动提高到 128Mi：
   `kubectl set resources deployment/trace-oom-api -n aiops-traced-oom --limits=memory=128Mi`
2. 若已存在 Secret：
   `kubectl set env deployment/trace-config-api -n aiops-traced-config PAYMENT_GATEWAY_TOKEN_FROM_SECRET=<SECRET_NAME>`

## 🧩 结构化修复计划
```json
{
  "remediation_available": true,
  "fix_type": "patch_workload_resources|patch_workload_env",
  "risk_level": "medium",
  "requires_human_approval": true,
  "issue_groups": [
    {
      "group_id": "g1-oom",
      "problem_type": "OOMKilled",
      "target": "aiops-traced-oom/trace-oom-api",
      "auto_fixable": true,
      "strategy": "自动增加 Deployment 内存 Limit 至 128Mi"
    },
    {
      "group_id": "g2-config",
      "problem_type": "ConfigError",
      "target": "aiops-traced-config/trace-config-api",
      "auto_fixable": true,
      "strategy": "自动注入未知 Secret"
    }
  ],
  "basis": [
    "Metrics Max 70.9Mi > 80Mi Limit",
    "required config PAYMENT_GATEWAY_TOKEN is missing"
  ],
  "actions": [
    {
      "id": "a1",
      "type": "kubectl_set",
      "group_id": "g1-oom",
      "description": "增加内存 Limit 至 128Mi",
      "execute_command": "kubectl set resources deployment/trace-oom-api -n aiops-traced-oom --limits=memory=128Mi"
    },
    {
      "id": "a2",
      "type": "kubectl_set",
      "group_id": "g2-config",
      "description": "注入未知 Secret",
      "execute_command": "kubectl set env deployment/trace-config-api -n aiops-traced-config PAYMENT_GATEWAY_TOKEN_FROM_SECRET=<SECRET_NAME>"
    }
  ],
  "stop_conditions": []
}
```
"""
    node = _node_with_response(report)

    result = node.execute(
        {
            "question": "我的集群有什么问题？",
            "layer": Layer.L2,
            "layer_analysis": '{"pod_abnormal_type":"CrashLoopBackOff"}',
            "evidence_analysis": _oom_and_unknown_secret_evidence(),
            "rca_analysis": "{}",
            "thinking_events": [],
        }
    )

    conclusion = result["conclusion"]
    plan = extract_remediation_plan(conclusion)

    assert plan is not None
    assert "128Mi" not in conclusion
    assert "PAYMENT_GATEWAY_TOKEN_FROM_SECRET" not in conclusion
    assert "<SECRET_NAME>" not in conclusion
    assert "70.9Mi > 80Mi" not in conclusion
    assert "未证明该请求直接触发 OOM" in conclusion
    assert all(group.get("auto_fixable") is False for group in plan.issue_groups)
    assert plan.actions == []
    assert plan.remediation_available is False
    assert plan.fix_type == "manual_only"


def test_ask_conclusion_does_not_synthesize_force_delete_without_finalizer_evidence():
    report = """
## 📊 诊断概览
Pod 删除卡住，但当前证据不足。

## 🛠️ 修复建议
```bash
kubectl delete pod terminating-stuck -n aiops-e2e --grace-period=0 --force
```

## 🧩 结构化修复计划
```json
{
  "remediation_available": false,
  "fix_type": "manual_only",
  "risk_level": "high",
  "requires_human_approval": true,
  "basis": ["finalizer evidence missing"],
  "actions": []
}
```
"""
    node = _node_with_response(report)

    result = node.execute(
        {
            "question": "我的集群有什么问题？",
            "layer": Layer.L1,
            "layer_analysis": '{"pod_abnormal_type":"TerminatingStuck"}',
            "evidence_analysis": "{}",
            "rca_analysis": "{}",
            "thinking_events": [],
        }
    )

    plan = extract_remediation_plan(result["conclusion"])

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.actions == []


def test_ask_conclusion_requires_upstream_finalizer_evidence_not_report_claims_only():
    report = """
## 📊 诊断概览
Pod terminating-stuck 当前 deletionTimestamp 已存在且 finalizers 非空。

## 🛠️ 修复建议
```bash
kubectl patch pod terminating-stuck -n aiops-e2e -p '{"metadata":{"finalizers":null}}' --type=merge
```

## 🧩 结构化修复计划
```json
{
  "remediation_available": false,
  "fix_type": "manual_only",
  "risk_level": "medium",
  "requires_human_approval": true,
  "basis": ["report claim only"],
  "actions": []
}
```
"""
    node = _node_with_response(report)

    result = node.execute(
        {
            "question": "我的集群有什么问题？",
            "layer": Layer.L1,
            "layer_analysis": '{"pod_abnormal_type":"TerminatingStuck"}',
            "evidence_analysis": "{}",
            "rca_analysis": "{}",
            "thinking_events": [],
        }
    )

    plan = extract_remediation_plan(result["conclusion"])

    assert plan is not None
    assert plan.remediation_available is False
    assert plan.actions == []


def test_ask_conclusion_repairs_invalid_structured_finalizer_action_when_evidence_is_safe():
    report = """
## 📊 诊断概览
Pod terminating-stuck 当前仍在 Terminating，deletionTimestamp 已存在且 finalizers 非空。

## 🛠️ 修复建议
```bash
kubectl patch pod terminating-stuck -n aiops-e2e -p '{"metadata":{"finalizers":null}}' --type=merge
```

## 🧩 结构化修复计划
```json
{
  "remediation_available": true,
  "fix_type": "remove_finalizer",
  "risk_level": "medium",
  "requires_human_approval": true,
  "basis": ["deletionTimestamp exists", "finalizers: aiops.e2e/hold"],
  "actions": [
    {
      "id": "a1",
      "type": "kubectl_patch",
      "description": "移除 finalizer",
      "risk": "medium",
      "dry_run_command": "kubectl patch pod terminating-stuck -n aiops-e2e -p '{\\"metadata\\":{\\"finalizers\\":null}}' --type=merge --dry-run=client -o yaml",
      "execute_command": "kubectl patch pod terminating-stuck -n aiops-e2e -p '{\\"metadata\\":{\\"finalizers\\":null}}' --type=merge",
      "verify_command": "kubectl get pod terminating-stuck -n aiops-e2e 2>&1 || echo NotFound"
    }
  ]
}
```
"""
    node = _node_with_response(report)

    result = node.execute(
        {
            "question": "我的集群有什么问题？",
            "layer": Layer.L1,
            "layer_analysis": '{"pod_abnormal_type":"TerminatingStuck"}',
            "evidence_analysis": _finalizer_evidence(),
            "rca_analysis": '{"root_cause":"Pod finalizer 清理卡住"}',
            "thinking_events": [],
        }
    )

    plan = extract_remediation_plan(result["conclusion"])

    assert plan is not None
    assert plan.remediation_available is True
    assert plan.actions[0].verify_command == "kubectl get pod terminating-stuck -n aiops-e2e"


def test_query_direct_render_does_not_invoke_ask_remediation_normalization():
    node = ConclusionFormatterNode(holmes_service=SimpleNamespace())
    node.workflow_config_override = {"query_mode": "direct"}
    node.ai_call = _PlainAICall("should not be called")

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("ask remediation normalization must not run for query direct")

    node._normalize_ask_remediation_plan = _fail_if_called

    result = node.execute(
        {
            "question": "查询 CPU",
            "layer": Layer.QUERY,
            "query_result": {
                "query_target": "查询 CPU",
                "collection_summary": "计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%",
                "columns": [{"key": "node", "label": "节点"}, {"key": "cpu", "label": "CPU"}],
                "rows": [{"node": "node1", "cpu": "1%"}],
                "notes": [],
                "missing": [],
                "sources": [{"tool": "execute_prometheus_instant_query", "query": "cpu"}],
            },
        }
    )

    assert "## 📊 查询结果" in result["conclusion"]
    assert "node1" in result["conclusion"]


def test_normalized_finalizer_plan_reaches_remediation_approval(monkeypatch):
    report = """
## 📊 诊断概览
Pod terminating-stuck 当前仍在 Terminating，deletionTimestamp 已存在且 finalizers 非空。

## 🛠️ 修复建议
```bash
kubectl patch pod terminating-stuck -n aiops-e2e -p '{"metadata":{"finalizers":null}}' --type=merge
```

## 🧩 结构化修复计划
```json
{
  "remediation_available": false,
  "fix_type": "manual_only",
  "risk_level": "medium",
  "requires_human_approval": true,
  "basis": ["deletionTimestamp exists", "finalizers: aiops.e2e/hold"],
  "actions": []
}
```
"""
    node = _node_with_response(report)
    normalized = node.execute(
        {
            "question": "我的集群有什么问题？",
            "layer": Layer.L1,
            "layer_analysis": '{"pod_abnormal_type":"TerminatingStuck"}',
            "evidence_analysis": _finalizer_evidence(),
            "rca_analysis": '{"root_cause":"Pod finalizer 清理卡住"}',
            "thinking_events": [],
        }
    )["conclusion"]

    class _DummyWorkflow:
        def stream(self, initial_state):
            return iter(
                [
                    {
                        "conclusion": {
                            "layer": "L1",
                            "conclusion_formatted": normalized,
                        }
                    }
                ]
            )

    monkeypatch.setattr(
        "app.core.workflow.executor.build_diagnosis_workflow",
        lambda *args, **kwargs: (_DummyWorkflow(), []),
    )

    executor = WorkflowExecutor(
        holmes_service=SimpleNamespace(
            workflow_config={
                "nodes": {"conclusion": True},
                "remediation": {
                    "enabled": True,
                    "executor": "deterministic",
                    "mode": "review",
                    "approval_timeout_seconds": 1,
                },
            },
            merged_catalog=None,
        )
    )

    events = list(executor.execute_stream("我的集群有什么问题？", run_id="run-normalized-plan"))

    approvals = [event for event in events if event["type"] == "remediation_approval_required"]
    assert approvals
    assert approvals[0]["approval_kind"] == "plan"
    assert approvals[0]["payload"]["actions"][0]["execute_command"].startswith(
        "kubectl patch pod terminating-stuck -n aiops-e2e"
    )
