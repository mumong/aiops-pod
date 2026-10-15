#!/usr/bin/env python3
"""Paired, read-only replay. No live cluster mutations or diagnostic special cases.

Use --source-dir with archived *.raw.txt responses. Outputs stay in an explicitly
chosen local experiment directory. --llm uses the deployed model configuration
without logging credentials. This is a consumption micro-eval, not full E2E.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import random
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.context.budget import estimate_tokens
from app.core.context.evidence_view import compact_json
from app.core.context.observation import ObservationProcessor


def cases(source: Path, selected: set[str] | None = None):
    definitions = [
        (
            "topology",
            "query_pod_topology",
            "001-evidence-query_pod_topology.raw.txt",
            "根据这次拓扑证据，workload Pod 的上级控制器完整链路是什么？给出最高控制器的 kind、name、uid，不要猜测。",
            ["ReplicaSet", "Deployment", "f8f0be25-af20-4992-b348-db64c693191b"],
        ),
        (
            "lifecycle",
            "query_pod_lifecycle",
            "001-layer-query_pod_lifecycle.raw.txt",
            "从这个 Pod 清单中找出最近终止原因为 OOMKilled 的 Pod，告诉我 namespace、name、终止原因。明确能否从累计重启数得到近10分钟重启次数。",
            ["aiops-case-08", "workload-5c9c7b6489-8ttw5", "OOMKilled"],
        ),
        (
            "metrics",
            "execute_pod_promql",
            "003-evidence-execute_pod_promql.raw.txt",
            "查询证据中 container_memory_working_set_bytes 各序列最后样本时间和值（保持 bytes）；按时间找最新的那条，列出原始值、单位、时间、节点，不要将不同时间容器实例相加。",
            ["44908544", "03:39:50", "node2"],
        ),
        (
            "tracing",
            "query_pod_tracing",
            "005-evidence-query_pod_tracing.raw.txt",
            "trace_id=145698f7fe9e75a11c95e02c63279b99 关联了哪些 flow 与 application span？给出各自 span_id、HTTP 状态及已有耗时，区分单位，不把单条成功请求当作整个服务健康。",
            ["e3448de871cb8306", "c601746cd0a506a6", "200"],
        ),
        (
            "structured_logs",
            "query_pod_logs",
            "002-evidence-query_pod_logs.raw.txt",
            "最新一条 memory allocation advanced 日志的 allocated_mib、trace_id 和采集时间是多少？这次日志是否是后端全部命中记录，还是只返回了部分？",
            ["48", "e9fe9a7cd3cd1eb54077e3872132139a", "03:40:03"],
        ),
        (
            "recovered_pod",
            "query_pod_lifecycle",
            "../recovered-tools/001-query_collect-query_pod_lifecycle.raw.txt",
            "这份生命周期快照中 workload Pod 现在 Ready 吗？最近一次终止原因和时间是什么？能否因此认定从未发生异常？",
            ["OOMKilled", "03:22:14", "Running"],
        ),
        (
            "real_small",
            "kubectl_get_by_kind_in_namespace",
            "../small-tools/001-query_collect-kubectl_get_by_kind_in_namespace.raw.txt",
            "根据这次 xnet 命名空间查询列出所有 Pod 及节点。",
            ["chartmuseum", "ham-dpkwq", "ham-h8sft", "ham-nnvzq"],
        ),
        (
            "native_metric",
            "execute_prometheus_instant_query",
            "../native-metrics-tools/002-query_collect-execute_prometheus_instant_query.raw.txt",
            "这次 Prometheus 查询的值和原始时间戳是多少？没有提供 PromQL 时能否确认其计算口径？",
            ["22.643904198471404", "1791450683.815"],
        ),
    ]
    result = []
    for name, tool, filename, question, expected in definitions:
        path = source / filename
        if selected is not None and name not in selected:
            continue
        if not path.is_file():
            raise FileNotFoundError(f"Required replay fixture missing for {name}: {path}")
        result.append(
            dict(
                name=name,
                tool=tool,
                raw=path.read_text(),
                question=question,
                expected=expected,
                origin="archived_real_run",
            )
        )
    result += [
        dict(
            name="small",
            tool="custom_inventory",
            origin="synthetic",
            raw='{"status":"success","items":[{"name":"alpha","ready":true},{"name":"beta","ready":false}]}',
            question="清单里有哪些对象，各自 ready 是什么？",
            expected=["alpha", "beta"],
        ),
        dict(
            name="late_log",
            tool="kubectl_logs",
            origin="synthetic",
            raw="INFO heartbeat\n" * 2000
            + "ERROR request_code=731 failed\n"
            + "INFO request_code=731 recovered\n"
            + "INFO heartbeat\n" * 10,
            question="日志最后一次异常的 request_code 是多少？之后有没有恢复证据？",
            expected=["731"],
        ),
        dict(
            name="long_series",
            tool="execute_prometheus_range_query",
            origin="synthetic",
            raw=compact_json(
                {
                    "status": "success",
                    "data": {
                        "resultType": "matrix",
                        "result": [
                            {
                                "metric": {"instance": "test-node", "__name__": "example_gauge"},
                                "values": [[1700000000 + i, str(i)] for i in range(1000)],
                            }
                        ],
                    },
                }
            ),
            question="这份样本里 example_gauge 最后一个点的原始时间戳和值是什么，instance 是什么？",
            expected=["1700000999", "999", "test-node"],
        ),
        dict(
            name="unknown_tool",
            tool="future_generic_tool",
            origin="synthetic",
            raw=compact_json(
                {
                    "status": "success",
                    "records": [
                        {
                            "id": i,
                            "site": "same-site" * 50,
                            "value": 0 if i == 99 else i,
                            "available": False if i == 99 else True,
                        }
                        for i in range(100)
                    ],
                }
            ),
            question="记录 id=99 的 value 和 available 各是多少？零值与 false 是否是实际返回？",
            expected=["99", "false"],
        ),
        dict(
            name="tabular",
            tool="kubectl_get_by_kind_in_namespace",
            origin="synthetic",
            raw="NAME READY STATUS RESTARTS AGE\n"
            + "".join(f"pod-{i} 1/1 Running {7 if i == 179 else 0} 2d\n" for i in range(180)),
            question="清单里的 pod-179 的状态和累计重启数是什么？这个清单能证明过去10分钟的重启次数吗？",
            expected=["pod-179", "Running", "7"],
        ),
    ]
    if selected is not None:
        available = {case["name"] for case in result}
        if selected - available:
            raise ValueError(f"Unknown cases: {sorted(selected - available)}")
        result = [case for case in result if case["name"] in selected]
    return result


def archive_reader(mode, archive_root):
    """Use the real schemas/descriptions in both arms, not a test-only wrapper."""
    from app.core.aicall.builtin_tools import LegacyReadContextArchiveTool, ReadContextArchiveTool

    reader_type = ReadContextArchiveTool if mode == "compact" else LegacyReadContextArchiveTool
    return reader_type(allowed_roots=[str(archive_root)])


def validate_answer(value):
    from app.core.workflow.query_contract import QueryAnswer, parse_query_answer

    if isinstance(value, str):
        parsed, _ = parse_query_answer(value)
        return parsed if parsed is not None else value, parsed is not None
    try:
        return QueryAnswer.model_validate(value).model_dump(), True
    except (ValueError, TypeError):
        return value, False


def model_config():
    raw = subprocess.check_output(
        ["kubectl", "get", "secret", "aiops-secret", "-n", "aiops", "-o", "json"]
    )
    values = json.loads(raw)["data"]
    config = {k: base64.b64decode(v).decode() for k, v in values.items() if k.startswith("LLM_")}
    return config


def consume(case, mode, observation, archive_root, config):
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
    from langchain_openai import ChatOpenAI

    from app.core.aicall.client import _parse_model
    from app.core.prompts import QUERY_COLLECT_PROMPT
    from app.core.workflow.query_contract import QueryAnswer

    read_tool = archive_reader(mode, archive_root)
    model_name, base_url = _parse_model(config["LLM_MODEL"], config["LLM_API_BASE"])
    model = ChatOpenAI(
        model=model_name,
        base_url=base_url,
        api_key=config["LLM_API_KEY"],
        timeout=90,
        max_retries=0,
        reasoning_effort=config.get("LLM_REASONING_EFFORT", "low"),
        max_tokens=2000,
    )
    model = model.bind_tools([read_tool, QueryAnswer])
    messages = [
        SystemMessage(content=QUERY_COLLECT_PROMPT),
        HumanMessage(content=case["question"] + "\n本次为冻结证据回放，不代表当前实时环境。"),
        AIMessage(content="", tool_calls=[{"name": case["tool"], "args": {}, "id": "source"}]),
        ToolMessage(content=observation["summary"], tool_call_id="source"),
    ]
    start = time.monotonic()
    details = {
        "model_calls": 0,
        "reads": [],
        "usage": {"input_tokens": 0, "output_tokens": 0},
        "answer": None,
        "execution_incomplete": None,
        "answer_contract_valid": False,
    }
    for _ in range(8):
        response = model.invoke(messages)
        details["model_calls"] += 1
        usage = response.usage_metadata or {}
        for key in details["usage"]:
            details["usage"][key] += int(usage.get(key, 0))
        messages.append(response)
        if not response.tool_calls:
            details["answer"], details["answer_contract_valid"] = validate_answer(response.content)
            break
        for call in response.tool_calls:
            if call["name"] == "QueryAnswer":
                details["answer"], details["answer_contract_valid"] = validate_answer(call["args"])
                break
            if call["name"] != "read_context_archive":
                content = "Error: only archived evidence is available in this paired replay"
            else:
                t = time.monotonic()
                try:
                    content = read_tool.invoke(call["args"])
                except Exception as exc:
                    content = f"Error: {type(exc).__name__}"
                details["reads"].append(
                    {
                        "args": call["args"],
                        "chars": len(content),
                        "seconds": time.monotonic() - t,
                        "result": content,
                    }
                )
            messages.append(ToolMessage(content=content, tool_call_id=call["id"]))
        if details["answer"] is not None:
            break
    if details["answer"] is None:
        details["execution_incomplete"] = "step_limit"
    elif not details["answer_contract_valid"]:
        details["execution_incomplete"] = "invalid_answer_contract"
    rendered = compact_json(details["answer"]).lower()
    rendered = re.sub(r"(?<=\d),(?=\d{3}(?:\D|$))", "", rendered)
    details.update(
        seconds=time.monotonic() - start,
        expected_tokens_found={s: s.lower() in rendered for s in case["expected"]},
    )
    # These token checks are screening only; human review of factual associations
    # and absence claims remains required before any rollout decision.
    return details


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--llm", action="store_true")
    p.add_argument("--cases", default="")
    p.add_argument("--modes", default="legacy,raw,compact")
    p.add_argument("--repeats", type=int, default=1)
    p.add_argument("--view-tokens", type=int, default=4096)
    p.add_argument("--seed", type=int, default=917)
    args = p.parse_args()
    selected_cases = cases(args.source_dir, set(args.cases.split(",")) if args.cases else None)
    modes = args.modes.split(",")
    if not modes or any(mode not in {"legacy", "raw", "compact"} for mode in modes):
        p.error("--modes must contain only legacy,raw,compact")
    if args.repeats < 1:
        p.error("--repeats must be positive")
    if args.output.exists() and any(args.output.iterdir()):
        p.error("--output must be empty; preserve prior trial evidence")
    args.output.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    config = model_config() if args.llm else None
    if config:
        print("MODEL", config["LLM_MODEL"], config.get("LLM_REASONING_EFFORT", "low"), flush=True)
    rows = []
    for case in selected_cases:
        for repeat in range(args.repeats):
            execution_order = modes[:]
            rng.shuffle(execution_order)
            for mode in execution_order:
                processor = ObservationProcessor(
                    archive_root=str(args.output / "archives"),
                    evidence_view_mode="compact" if mode == "compact" else "legacy",
                    evidence_view_tokens=args.view_tokens,
                )
                start = time.monotonic()
                observation = processor.process(
                    f"{case['name']}-{mode}-{repeat}",
                    "query_collect",
                    1,
                    case["tool"],
                    case["raw"],
                    preserve_raw=True,
                )
                if mode == "raw":
                    observation["summary"] = case["raw"]
                row = {
                    "case": case["name"],
                    "mode": mode,
                    "repeat": repeat,
                    "view_budget": args.view_tokens,
                    "seed": args.seed,
                    "mode_order": execution_order,
                    "source_sha256": hashlib.sha256(case["raw"].encode()).hexdigest(),
                    "question": case["question"],
                    "origin": case["origin"],
                    "raw_tokens_est": estimate_tokens(case["raw"]),
                    "view_tokens_est": estimate_tokens(observation["summary"]),
                    "projection_ms": round(1000 * (time.monotonic() - start), 3),
                }
                if config:
                    try:
                        row["llm"] = consume(
                            case, mode, observation, args.output / "archives", config
                        )
                    except Exception as exc:
                        row["llm_error_type"] = type(exc).__name__
                rows.append(row)
                (args.output / f"{case['name']}-{mode}-{repeat}.json").write_text(
                    json.dumps(row, ensure_ascii=False, indent=2)
                )
                brief = {k: v for k, v in row.items() if k != "llm"}
                if "llm" in row:
                    d = row["llm"]
                    brief.update(
                        seconds=round(d["seconds"], 2),
                        reads=len(d["reads"]),
                        answer_contract_valid=d["answer_contract_valid"],
                        expected_tokens_found=d["expected_tokens_found"],
                    )
                print(json.dumps(brief, ensure_ascii=False), flush=True)
    (args.output / "results.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
