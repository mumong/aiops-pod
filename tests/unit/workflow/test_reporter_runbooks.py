import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.core.skills.models import Layer
from app.core.workflow.metrics import WorkflowMetrics
from app.core.workflow.reporter import update_metrics_from_state


def _make_catalog():
    return SimpleNamespace(
        catalog=[
            SimpleNamespace(
                id="l2-oomkilled",
                link="l2-oomkilled.md",
                description="【L2】Pod OOMKilled (Exit Code 137) — 容器内存超过 cgroup limits 被 OOM Killer 终止",
            ),
            SimpleNamespace(
                id="private-k8s-health-reference",
                link="private-k8s-health-reference.md",
                description="【通用】私有化 Kubernetes 环境健康与高效排查参考手册 — 适用于 Calico + NFS + containerd 环境",
            ),
        ]
    )


def test_reporter_only_displays_catalog_runbooks():
    metrics = WorkflowMetrics(run_id="r1", question="我的集群有什么问题")
    state = {
        "layer": Layer.L2,
        "conclusion": "当前发现 memhog Pod OOMKilled。",
        "rca_analysis": '{"primary_runbooks":["Pod Running，但 Service 没有 Endpoints"]}',
        "evidence_analysis": "{}",
        "thinking_events": [
            {
                "type": "tool_result",
                "status": "success",
                "tool_name": "fetch_runbook",
                "result_preview": "<runbook>\n# 私有化 Kubernetes 环境健康与高效排查参考手册\n...\n</runbook>",
            }
        ],
        "evidence_items": [],
        "tool_results": [],
        "llm_calls": 1,
    }

    update_metrics_from_state(metrics, state, runbook_catalog=_make_catalog())

    assert metrics.runbook_id == "private-k8s-health-reference"
    assert metrics.primary_runbook == "private-k8s-health-reference"


def test_reporter_normalizes_known_scene_runbook_title_to_catalog_id():
    metrics = WorkflowMetrics(run_id="r2", question="为什么 OOM")
    state = {
        "layer": Layer.L2,
        "conclusion": "容器被 OOMKilled。",
        "rca_analysis": '{"primary_runbooks":["L2 Pod OOMKilled (Exit Code 137)"]}',
        "evidence_analysis": "{}",
        "thinking_events": [
            {
                "type": "tool_result",
                "status": "success",
                "tool_name": "fetch_runbook",
                "result_preview": "<runbook>\n# L2 Pod OOMKilled (Exit Code 137)\n...\n</runbook>",
            }
        ],
        "evidence_items": [],
        "tool_results": [],
        "llm_calls": 1,
    }

    update_metrics_from_state(metrics, state, runbook_catalog=_make_catalog())

    assert metrics.primary_runbook == "l2-oomkilled"
    assert metrics.runbook_id == "l2-oomkilled"


def test_reporter_keeps_multiple_catalog_runbooks_when_multiple_are_fetched():
    metrics = WorkflowMetrics(run_id="r3", question="我的集群有什么问题")
    state = {
        "layer": Layer.L2,
        "conclusion": "当前同时参考了通用基线与 OOM 场景 runbook。",
        "rca_analysis": '{"primary_runbooks":["L2 Pod OOMKilled (Exit Code 137)"]}',
        "evidence_analysis": "{}",
        "thinking_events": [
            {
                "type": "tool_result",
                "status": "success",
                "tool_name": "fetch_runbook",
                "result_preview": "<runbook>\n# 私有化 Kubernetes 环境健康与高效排查参考手册\n...\n</runbook>",
            },
            {
                "type": "tool_result",
                "status": "success",
                "tool_name": "fetch_runbook",
                "result_preview": "<runbook>\n# L2 Pod OOMKilled (Exit Code 137)\n...\n</runbook>",
            },
        ],
        "evidence_items": [],
        "tool_results": [],
        "llm_calls": 1,
    }

    update_metrics_from_state(metrics, state, runbook_catalog=_make_catalog())

    assert metrics.primary_runbook == "l2-oomkilled"
    assert metrics.runbook_id == "l2-oomkilled, private-k8s-health-reference"
