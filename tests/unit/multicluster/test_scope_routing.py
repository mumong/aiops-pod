"""AIOps cluster scope: routing, clarification, follow-ups, tool binding (spec FR-005..FR-008)."""

import asyncio
from types import SimpleNamespace

import pytest
from langchain_core.tools import StructuredTool

from app.core import multicluster
from app.core.workflow.nodes.request_router import RequestContract, RequestRouterNode

EDGE88 = "vc-942nkkozc8o5fyb9q3bznb1ws"
EDGE89 = "vc-dluw0jousipr6h5co2bwpyqk2"
CENTER = "vc-xnet-management"
CONFIG = f"""
clusters:
  center: {CENTER}
  items:
    - {{name: {CENTER}, aliases: [center, 中心集群], access: local, observability: victoria}}
    - {{name: {EDGE88}, aliases: [edge-88], access: xnet, observability: victoria}}
    - {{name: {EDGE89}, aliases: [edge-89], access: xnet, observability: victoria}}
  access:
    xnet: {{proxy_url: "https://x/proxy", runner_url: "http://r:8090"}}
"""


@pytest.fixture
def multi(tmp_path, monkeypatch):
    path = tmp_path / "clusters.yaml"
    path.write_text(CONFIG)
    monkeypatch.setenv("AIOPS_CLUSTERS_CONFIG", str(path))
    multicluster.reset()
    yield
    multicluster.reset()


@pytest.fixture
def single(tmp_path, monkeypatch):
    monkeypatch.setenv("AIOPS_CLUSTERS_CONFIG", str(tmp_path / "absent.yaml"))
    multicluster.reset()
    yield
    multicluster.reset()


def route(contract_values, history=None, *, capture=None):
    def classify(**kwargs):
        if capture is not None:
            capture.append(kwargs)
        return kwargs["schema"](**contract_values), ""

    node = RequestRouterNode()
    node.ai_call = SimpleNamespace(call_structured=classify)
    # These tests are about resolution; phrase a question that names the scope
    # (grounding has its own tests below).
    names = [n for n in contract_values.get("clusters") or [] if not n.startswith("*")]
    state = {"question": f"查看 {' '.join(names)} 全部集群 中心集群 的情况"}
    if history:
        state["query_session_context"] = {"turns": history}
    return node.execute(state)


BASE = dict(route="focused", task="query", scope="cluster")


# --- single-cluster deployments are untouched -------------------------------------------


def test_single_cluster_uses_the_original_schema_and_prompt(single):
    from app.core.prompts import REQUEST_ROUTER_PROMPT

    calls = []
    result = route(BASE, capture=calls)
    assert calls[0]["schema"] is RequestContract
    assert calls[0]["system_prompt"] == REQUEST_ROUTER_PROMPT
    assert result["request_route"] == "focused"
    assert "clusters" not in result["request_contract"]


def test_single_cluster_tools_are_not_wrapped(single):
    tools = [_tool("kubectl_get")]
    assert multicluster.scoped_tools(tools, {"request_contract": {}}) is tools


# --- multi-cluster routing ---------------------------------------------------------------


def test_multi_cluster_router_sees_cluster_list(multi):
    calls = []
    route({**BASE, "cluster_mode": "single", "clusters": ["edge-88"]}, capture=calls)
    prompt = calls[0]["system_prompt"]
    assert EDGE88 in prompt and "edge-88" in prompt and "中心集群" in prompt
    assert "clusters" in calls[0]["schema"].model_fields


@pytest.mark.parametrize(
    "mode,names,expected",
    [
        ("single", ["edge-88"], [EDGE88]),
        ("single", ["EDGE-89"], [EDGE89]),
        ("multiple", ["edge-88", "edge-89"], [EDGE88, EDGE89]),
        ("multiple", ["*"], [CENTER, EDGE88, EDGE89]),
        # Run e43e8298: "所有边缘测集群" must not include the center.
        ("multiple", ["*edge"], [EDGE88, EDGE89]),
        ("center", [], [CENTER]),
        ("center", ["中心集群"], [CENTER]),
    ],
)
def test_scopes_resolve_to_canonical_names(multi, mode, names, expected):
    result = route({**BASE, "cluster_mode": mode, "clusters": names})
    assert result["request_route"] == "focused"
    assert result["request_contract"]["clusters"] == expected


def test_unspecified_scope_is_clarified_without_tools(multi):
    result = route({**BASE, "cluster_mode": "unspecified", "clusters": []})
    assert result["request_route"] == "clarify"
    assert "中心集群" in result["conclusion"] and "edge-88" in result["conclusion"]
    assert "全部集群" in result["conclusion"]


def test_mode_without_clusters_is_clarified(multi):
    result = route({**BASE, "cluster_mode": "single", "clusters": []})
    assert result["request_route"] == "clarify"


def test_model_route_is_overridden_when_scope_missing(multi):
    result = route(
        {
            "route": "full_diagnosis",
            "task": "diagnose",
            "scope": "namespace",
            "cluster_mode": "unspecified",
            "clusters": [],
        }
    )
    assert result["request_route"] == "clarify"


def test_unknown_cluster_lists_available(multi):
    result = route({**BASE, "cluster_mode": "single", "clusters": ["edge-99"]})
    assert result["request_route"] == "clarify"
    assert "edge-99" in result["conclusion"] and "edge-88" in result["conclusion"]


def test_repair_over_several_clusters_is_not_supported(multi):
    result = route(
        {
            "route": "remediation",
            "task": "repair",
            "scope": "cluster",
            "cluster_mode": "multiple",
            "clusters": ["edge-88", "edge-89"],
        }
    )
    assert result["request_route"] == "clarify"
    assert "一个集群" in result["conclusion"]


def test_unsupported_and_model_clarify_are_kept(multi):
    assert (
        route(
            {
                "route": "unsupported",
                "task": "unsupported",
                "scope": "unspecified",
                "cluster_mode": "unspecified",
                "clusters": [],
            }
        )["request_route"]
        == "stop"
    )
    out = route(
        {
            "route": "clarify",
            "task": "query",
            "scope": "unspecified",
            "clarification": "哪个命名空间？",
            "cluster_mode": "single",
            "clusters": ["edge-88"],
        }
    )
    assert out["request_route"] == "clarify" and out["conclusion"] == "哪个命名空间？"


def test_follow_up_history_carries_clusters(multi):
    calls = []
    history = [
        {
            "question": "edge-89 有哪些 Pod 异常",
            "answer": "...",
            "request_contract": {"clusters": [EDGE89], "cluster_mode": "single"},
        }
    ]
    route({**BASE, "cluster_mode": "single", "clusters": [EDGE89]}, history, capture=calls)
    assert EDGE89 in calls[0]["question"]


def test_repair_entry_keeps_source_clusters(multi):
    node = RequestRouterNode()
    node.ai_call = SimpleNamespace(call_structured=lambda **k: pytest.fail("no model call"))
    out = node.execute(
        {
            "question": "生成修复方案",
            "repair_entry_requested": True,
            "repair_context": {
                "diagnosis": {
                    "payload": {
                        "request_contract": {
                            "scope": "namespace",
                            "namespaces": ["aiops-case-09"],
                            "clusters": [EDGE88],
                            "cluster_mode": "single",
                        }
                    }
                }
            },
        }
    )
    assert out["request_contract"]["clusters"] == [EDGE88]


# --- tool binding ------------------------------------------------------------------------


def _tool(name, seen=None):
    def run(**kwargs):
        if seen is not None:
            seen.append(kwargs)
        return f"ok {kwargs.get('cluster')}"

    async def arun(**kwargs):
        return run(**kwargs)

    schema = {
        "type": "object",
        "properties": {"kind": {"type": "string"}, "cluster": {"type": "string"}},
    }
    return StructuredTool.from_function(
        func=run, coroutine=arun, name=name, description="d", args_schema=schema
    )


def test_single_scope_forces_the_cluster(multi):
    seen = []
    tools = multicluster.scoped_tools(
        [_tool("kubectl_get", seen)],
        {"request_contract": {"clusters": [EDGE88], "cluster_mode": "single"}},
    )
    out = asyncio.run(tools[0].ainvoke({"kind": "pod", "cluster": "edge-89"}))
    assert seen[-1]["cluster"] == EDGE88 and EDGE88 in out


def test_multi_scope_requires_a_cluster_in_scope(multi):
    seen = []
    state = {"request_contract": {"clusters": [EDGE88, EDGE89], "cluster_mode": "multiple"}}
    tool = multicluster.scoped_tools([_tool("kubectl_get", seen)], state)[0]
    assert "cluster_required" in asyncio.run(tool.ainvoke({"kind": "pod"}))
    assert "cluster_out_of_scope" in asyncio.run(
        tool.ainvoke({"kind": "pod", "cluster": "center"})
    )
    assert EDGE89 in asyncio.run(tool.ainvoke({"kind": "pod", "cluster": "edge-89"}))
    assert [call["cluster"] for call in seen] == [EDGE89]


def test_lane_group_cluster_wins(multi):
    seen = []
    state = {"request_contract": {"clusters": [EDGE88, EDGE89]}, "group": {"cluster": EDGE89}}
    tool = multicluster.scoped_tools([_tool("kubectl_get", seen)], state)[0]
    asyncio.run(tool.ainvoke({"kind": "pod"}))
    assert seen[-1]["cluster"] == EDGE89


def test_tools_without_cluster_parameter_are_left_alone(multi):
    plain = StructuredTool.from_function(func=lambda x: x, name="calc", description="d")
    assert (
        multicluster.scoped_tools([plain], {"request_contract": {"clusters": [EDGE88]}})[0]
        is plain
    )


def test_sync_invocation_is_scoped_too(multi):
    seen = []
    tool = multicluster.scoped_tools(
        [_tool("kubectl_get", seen)], {"request_contract": {"clusters": [EDGE88]}}
    )[0]
    tool.invoke({"kind": "pod"})
    assert seen[-1]["cluster"] == EDGE88


def test_kubectl_env_for_remote_clusters(multi):
    assert multicluster.kubectl_env(EDGE88)["AIOPS_CLUSTER"] == EDGE88
    assert multicluster.kubectl_env(CENTER) is None
    assert multicluster.kubectl_env(None) is None


# --- call sites --------------------------------------------------------------------------


def test_run_argv_targets_remote_cluster_through_the_shim(multi, monkeypatch):
    import subprocess

    from app.core.remediation import pod_executor

    calls = []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs.get("env") or {}))
        return subprocess.CompletedProcess(argv, 0, "out", "")

    monkeypatch.setattr(pod_executor.subprocess, "run", fake_run)
    assert pod_executor.run_argv(["kubectl", "get", "pods"], cluster=EDGE88) == "out"
    argv, env = calls[-1]
    assert env["AIOPS_CLUSTER"] == EDGE88
    assert "aiops-kube-" not in env.get(
        "KUBECONFIG", ""
    )  # no in-cluster kubeconfig for a remote cluster


def test_graph_wrapper_binds_tools_to_the_run_scope(multi):
    from app.core.workflow.graph import _wrap_node_execute

    seen = []

    class Node:
        node_id, node_name = "n", "n"
        tools = [_tool("kubectl_get", seen)]

        def execute(self, state):
            asyncio.run(self.tools[0].ainvoke({"kind": "pod"}))
            return {}

    node = Node()
    _wrap_node_execute(node)(
        {"request_contract": {"clusters": [EDGE89], "cluster_mode": "single"}}
    )
    assert seen[-1]["cluster"] == EDGE89
    # a second run with another scope rebinds from the original tools
    _wrap_node_execute(node)(
        {"request_contract": {"clusters": [EDGE88], "cluster_mode": "single"}}
    )
    assert seen[-1]["cluster"] == EDGE88


# --- grounding: the scope must come from the user's words or the conversation -------------


def route_q(question, contract_values, history=None):
    def classify(**kwargs):
        return kwargs["schema"](**contract_values), ""

    node = RequestRouterNode()
    node.ai_call = SimpleNamespace(call_structured=classify)
    state = {"question": question}
    if history:
        state["query_session_context"] = {"turns": history}
    return node.execute(state)


@pytest.mark.parametrize(
    "question,mode,names,expected",
    [
        ("所有集群的节点状态", "multiple", ["*"], [CENTER, EDGE88, EDGE89]),
        ("检查每个集群", "multiple", ["*"], [CENTER, EDGE88, EDGE89]),
        ("全部集群有什么问题", "multiple", ["*"], [CENTER, EDGE88, EDGE89]),
        ("中心集群的 vmagent 正常吗", "center", [], [CENTER]),
        ("Edge-88 上的 Pod", "single", ["edge-88"], [EDGE88]),
        (f"{EDGE89} 有几个 Pod", "single", [EDGE89], [EDGE89]),
    ],
)
def test_grounded_scopes_are_accepted(multi, question, mode, names, expected):
    out = route_q(question, {**BASE, "cluster_mode": mode, "clusters": names})
    assert out["request_route"] == "focused" and out["request_contract"]["clusters"] == expected


def test_follow_up_is_grounded_by_history(multi):
    history = [
        {
            "question": "edge-89 有哪些 Pod 异常",
            "answer": "...",
            "request_contract": {"clusters": [EDGE89], "cluster_mode": "single"},
        }
    ]
    out = route_q(
        "那它的事件呢", {**BASE, "cluster_mode": "single", "clusters": [EDGE89]}, history
    )
    assert out["request_route"] == "focused" and out["request_contract"]["clusters"] == [EDGE89]


def test_answer_to_the_scope_question_is_grounded(multi):
    history = [
        {
            "question": "有哪些 Pod 异常",
            "answer": "请说明要查看的范围…",
            "request_contract": {"clusters": [], "cluster_mode": "unspecified"},
        }
    ]
    out = route_q("edge-89", {**BASE, "cluster_mode": "single", "clusters": ["edge-89"]}, history)
    assert out["request_contract"]["clusters"] == [EDGE89]


def test_contract_carries_display_labels_set_by_code(multi):
    out = route(
        {
            **BASE,
            "cluster_mode": "multiple",
            "clusters": ["edge-88", EDGE89],
            "cluster_labels": ["made-up"],
        }
    )
    assert out["request_contract"]["cluster_labels"] == ["edge-88", "edge-89"]
    out = route({**BASE, "cluster_mode": "center", "clusters": []})
    assert out["request_contract"]["cluster_labels"] == ["center"]


# --- inventory: questions about the clusters themselves (run 6de07c004813430e) -----------


def test_cluster_inventory_question_is_answered_not_clarified(multi):
    out = route_q("我现在有哪些集群？", {**BASE, "cluster_mode": "inventory", "clusters": []})
    assert out["request_route"] == "focused"
    assert out["request_contract"]["cluster_mode"] == "inventory"
    assert out["request_contract"]["clusters"] == [CENTER, EDGE88, EDGE89]


def test_inventory_with_status_follow_up_keeps_all_clusters(multi):
    out = route_q(
        "各个子集群的状态怎么样", {**BASE, "cluster_mode": "inventory", "clusters": ["*"]}
    )
    assert out["request_route"] == "focused" and len(out["request_contract"]["clusters"]) == 3


def test_router_prompt_describes_inventory(multi):
    assert "inventory" in multicluster.router_prompt()


def test_quick_query_exposes_list_clusters():
    from app.core.workflow.nodes.query_answer import QueryCollectNode

    assert "list_clusters" in QueryCollectNode.READ_TOOLS


# --- intent-based scope (Boss 2026-10-22: understand intent, do not gate on wording) ----


def test_questions_needing_no_cluster_are_answered_without_asking(multi):
    out = route_q(
        "什么是 CrashLoopBackOff？",
        {
            "route": "focused",
            "task": "explain",
            "scope": "unspecified",
            "cluster_mode": "none",
            "clusters": [],
        },
    )
    assert out["request_route"] == "focused"
    assert (
        out["request_contract"]["clusters"] == []
        and out["request_contract"]["cluster_mode"] == "none"
    )


def test_inventory_is_trusted_from_intent_without_keywords(multi):
    out = route_q("接入了哪些环境？", {**BASE, "cluster_mode": "inventory", "clusters": []})
    assert out["request_route"] == "focused" and len(out["request_contract"]["clusters"]) == 3


def test_all_clusters_is_trusted_from_intent(multi):
    out = route_q("整体看一下情况", {**BASE, "cluster_mode": "multiple", "clusters": ["*"]})
    assert out["request_route"] == "focused" and len(out["request_contract"]["clusters"]) == 3


def test_unspecified_scope_still_asks(multi):
    out = route_q("有哪些 Pod 异常", {**BASE, "cluster_mode": "unspecified", "clusters": []})
    assert out["request_route"] == "clarify" and out["request_contract"]["cluster_labels"] == []


def test_router_prompt_states_principles_not_sample_questions(multi):
    """Boss 2026-10-22: no special handling; the model reads intent on its own.

    The prompt defines the modes and selectors; it must not quote the questions
    that the intent measurement asks (that would teach to the test).
    """
    import json
    from pathlib import Path

    prompt = multicluster.router_prompt()
    for mode in ("none", "inventory", "single", "multiple", "center", "unspecified"):
        assert mode in prompt, mode
    samples = json.loads(
        (
            Path(__file__).resolve().parents[3]
            / "scripts/acceptance/multicluster/intent_cases.json"
        ).read_text()
    )["cases"]
    for case in samples:
        assert case["question"].rstrip("？?") not in prompt, case["question"]


def test_router_prompt_names_roles_and_the_edge_selector(multi):
    prompt = multicluster.router_prompt()
    assert prompt.count("：中心集群") == 1
    assert prompt.count("边缘集群（子集群）") == 2
    assert '["*edge"]' in prompt and "不含中心集群" in prompt
