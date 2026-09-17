"""Opt-in real-model/read-only-MCP smoke checks; does not deploy or change Pods.

Uses LLM_* environment variables. --secret-file explicitly loads a Kubernetes
Secret manifest locally without printing its values. Artifacts are written only
to a newly created output directory. Full-diagnosis routing is tested without
executing the legacy cluster diagnostic workflow.
"""

import argparse
import asyncio
import json
import os
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml

from app.core.aicall.client import AICall
from app.core.aicall.tools import load_mcp_tools
from app.core.aicall.builtin_tools import get_builtin_tools
from app.core.workflow.nodes.request_router import RequestRouterNode
from app.core.workflow.nodes.focused import FocusedTaskNode
from app.core.workflow.executor import WorkflowExecutor


QUESTIONS = [
    ("global", "我的集群有什么问题？", "full_diagnosis"),
    ("logs_clarify", "查询下pod的日志", "query"),
    ("namespace_logs", "查询下xnet命名空间下所有pod的日志", "query"),
    ("namespace_health", "xnet 命名空间下有什么异常的 Pod 吗？", "focused"),
    ("namespace_metrics", "xnet 命名空间下所有 Pod 的 CPU 和 memory 实际使用量是多少？", "focused"),
    ("pod_diagnosis", "xnet 命名空间下的 test-nginx 有什么问题？不存在就明确告诉我。", "focused"),
    ("knowledge", "Pod OOMKilled 和探针失败导致的重启有什么区别？只解释原理，不查询集群。", "focused"),
    ("filtered_cluster", "集群里有哪些 Pending Pod？只列出名称和命名空间，不做根因诊断。", "focused"),
    ("mixed", "xnet 中哪个 Pod 内存使用量最高？结合它的 limit 分析是否有 OOM 风险。", "focused"),
    ("missing_namespace", "definitely-absent-aiops-test 命名空间有什么 Pod？不要查询其他命名空间。", "focused"),
    ("network", "xnet 命名空间各 Pod 最近 5 分钟的网络接收和发送速率分别是多少？请注明单位。", "focused"),
    ("logs", "查看 aiops-case-08 命名空间 workload Pod 最近的日志，说明实际看到的错误；无日志就说明。", "focused"),
    ("probe", "aiops-case-09 命名空间的 workload Pod 为什么没有 Ready？只检查这个命名空间。", "focused"),
    ("tracing", "aiops-case-09 命名空间 workload Pod 最近的 HTTP 请求有什么错误？查链路记录，不做全局排障。", "focused"),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--secret-file", type=Path)
    parser.add_argument("--config", type=Path, default=Path("deploy/configmap/config.yaml"))
    parser.add_argument("--mcp-host", help="Optional replacement for cluster-local MCP DNS when running locally")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cases", default="global,namespace_health,namespace_metrics,knowledge")
    parser.add_argument("--route-only", action="store_true")
    parser.add_argument("--query-direct", action="store_true", help="Exercise the /query two-agent graph without request routing")
    parser.add_argument("--executor", action="store_true", help="Run the real workflow executor for focused cases, including lifecycle/SSE events")
    parser.add_argument("--execute-full", action="store_true", help="Also execute an explicitly selected full-diagnosis case (read-only)")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    if args.secret_file:
        secret = yaml.safe_load(args.secret_file.read_text()).get("stringData", {})
        for key in ("LLM_API_KEY", "LLM_MODEL", "LLM_API_BASE", "MODEL_CONTEXT_WINDOW"):
            if key in secret:
                os.environ.setdefault(key, str(secret[key]))
    config = yaml.safe_load(args.config.read_text())
    if "data" in config and "config.yaml" in config["data"]:
        config = yaml.safe_load(config["data"]["config.yaml"])
    ai = AICall(model=os.environ["LLM_MODEL"], api_key=os.environ["LLM_API_KEY"],
                api_base=os.environ.get("LLM_API_BASE", ""),
                chat_model_extra_body=config.get("llm", {}).get("extra_body"))
    tools = []
    catalog = None
    if not args.route_only:
        servers = config.get("mcp_servers", {})
        for name, server in servers.items():
            if name not in {"k8s-mcp-service", "prometheus_tool", "aiops-observability-query"}:
                server["enabled"] = False
            if args.mcp_host and server.get("config", {}).get("url"):
                server["config"]["url"] = server["config"]["url"].replace(
                    "mcp-server-manager.mcp.svc.cluster.local", args.mcp_host)
        runbook_manifest = Path("deploy/configmap/runbooks.yaml")
        runbook_dirs = None
        if runbook_manifest.exists():
            runbook_dir = args.output / "runbooks"
            runbook_dir.mkdir()
            runbook_data = yaml.safe_load(runbook_manifest.read_text()).get("data") or {}
            catalog = SimpleNamespace(catalog=[SimpleNamespace(**item) for item in
                json.loads(runbook_data.get("catalog.json", "{}")).get("catalog", [])])
            for name, content in runbook_data.items():
                if name.endswith(".md") and Path(name).name == name:
                    (runbook_dir / name).write_text(content)
            runbook_dirs = [str(runbook_dir.resolve())]
        tools = asyncio.run(load_mcp_tools(servers)) + get_builtin_tools(runbook_dirs=runbook_dirs)
    selected = set(args.cases.split(","))
    unknown = selected - {item[0] for item in QUESTIONS}
    if unknown:
        parser.error(f"Unknown cases: {sorted(unknown)}")
    summary = []
    for case, question, expected in QUESTIONS:
        if case not in selected:
            continue
        run_id = f"task-smoke-{uuid.uuid4().hex[:12]}"
        router = RequestRouterNode()
        router.ai_call = ai
        router.current_run_id = run_id
        state = {"question": question, "run_id": run_id}
        if args.query_direct:
            expected = "query"
            state["request_route"] = "query"
        else:
            state.update(router.execute(state))
        print(f"{case}: route={state.get('request_route')} expected={expected} run_id={run_id}", flush=True)
        should_execute = args.query_direct or state.get("request_route") == "focused" or (
            state.get("request_route") == "full_diagnosis" and args.execute_full)
        if should_execute and not args.route_only:
            if args.executor or args.execute_full or args.query_direct:
                workflow_config = dict(config.get("workflow") or {})
                workflow_config["remediation"] = {"enabled": False}
                service = SimpleNamespace(merged_catalog=catalog, workflow_config=workflow_config,
                                          get_node_max_steps=lambda _: 16,
                                          get_prompt_language=lambda: "zh")
                executor = WorkflowExecutor(service)
                executor.ai_call = ai
                executor.mcp_tools = tools
                executor.REPORTS_DIR = str(args.output / "reports")
                stream_events = list(executor.execute_stream(question=question, run_id=run_id,
                                                             workflow_overrides={"query_mode": "direct" if args.query_direct else "auto"}))
                state["executor_events"] = stream_events
                final = next((e for e in reversed(stream_events) if e.get("type") == "final"), {})
                state["conclusion"] = final.get("answer", "")
                state["focused_result"] = final.get("focused_result")
                state["request_route"] = final.get("request_route", state.get("request_route"))
                state["request_contract"] = final.get("request_contract", state.get("request_contract"))
                if not final:
                    state["executor_error"] = "No final event"
            else:
                focused = FocusedTaskNode(SimpleNamespace(get_node_max_steps=lambda _: 16))
                focused.ai_call = ai
                focused.tools = tools
                focused.current_run_id = run_id
                state.update(focused.execute(state))
            print(state.get("conclusion", ""), flush=True)
        (args.output / f"{case}.json").write_text(json.dumps(state, ensure_ascii=False, indent=2, default=str))
        summary.append({"case": case, "run_id": run_id, "route": state.get("request_route"),
                        "expected_route": expected, "route_pass": state.get("request_route") == expected,
                        "missing": (state.get("focused_result") or {}).get("missing"),
                        "answer_review": "manual_review_required"})
    (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if all(item["route_pass"] for item in summary) else 1


if __name__ == "__main__":
    raise SystemExit(main())
