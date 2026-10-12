#!/usr/bin/env python3
"""Pre-tool paired experiment; no live MCP calls or serving configuration changes.

JMESPath is an evaluation dependency, not a new production tool. Run with the
existing development environment. Full responses/answers are saved for review;
the script deliberately does not equate keyword matches with factual correctness.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import sys
import time

import jmespath

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


MAX_EXPRESSION = 2048
MAX_RESULT_BYTES = 12000
METADATA = (
    "contract_version", "status", "source", "observed_at", "scope", "window",
    "coverage", "history_complete", "limitations", "next_continue_token",
    "remaining_item_count", "resource_version", "raw_ref",
)
FIELDS = (
    "Snapshot root: pods[]. Pod fields: namespace,name,uid,node,phase,reason,"
    "conditions[],containers[]. Container fields: name,role,status_observed,ready,"
    "restart_count_total,state,last_state,latest_observed_termination_at,"
    "termination_within_window,restart_count_in_window,resources. "
    "state/last_state may contain running,waiting,terminated. terminated contains "
    "reason,exitCode,signal,startedAt,finishedAt. resources has limits/requests. "
    "Missing status/time is unknown. Lifetime restart totals are not window counts. "
    "Running/Ready does not rule out a recent termination. Paging covers only the "
    "received snapshot; retain source coverage and history limitations."
)


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def compute(payload, expression, *, max_bytes=MAX_RESULT_BYTES):
    """Evaluate JSON only; deliberately not a production execution sandbox."""
    metadata = {key: copy.deepcopy(payload[key]) for key in METADATA if key in payload}
    if payload.get("status") != "success":
        return {"status": "error", "error": "source_not_successful", "source_metadata": metadata}
    if not isinstance(expression, str) or not expression.strip() or len(expression) > MAX_EXPRESSION:
        return {"status": "error", "error": "invalid_expression_length"}
    try:
        result = jmespath.search(expression, payload)
        result_bytes = len(encode(result).encode())
    except (jmespath.exceptions.JMESPathError, TypeError, ValueError, RecursionError) as exc:
        return {"status": "error", "error": type(exc).__name__, "detail": str(exc)[:500]}
    packet = {
        "status": "success", "source_metadata": metadata,
        "source_record_count": len(payload["pods"]) if isinstance(payload.get("pods"), list) else None,
        "executed_expression": expression,
        "result_kind": "null" if result is None else type(result).__name__,
        "result": result,
        "interpretation_limit": (
            "Result is computed over this received snapshot only, not missing pages. "
            "null may indicate an absent field; it does not prove no resources exist."
        ),
    }
    if len(encode(packet).encode()) > max_bytes:
        return {"status": "error", "error": "result_too_large", "result_bytes": result_bytes,
                "max_packet_bytes": max_bytes, "executed_expression": expression,
                "detail": "Select fewer fields or compute the requested statistic; result was not truncated."}
    return packet


def schema(mode):
    if mode == "records":
        from scripts.evidence_record_trial import record_schema

        return record_schema()
    props = {"namespace": {"type": "string", "description": "Optional exact namespace."},
             "pod": {"type": "string", "description": "Optional exact Pod; requires namespace."}}
    description = "Read frozen Pod lifecycle evidence (not current cluster data). " + FIELDS
    if mode == "compute":
        props["expression"] = {
            "type": "string", "description": (
                "Optional standard JMESPath on the snapshot root. Filter/project/count/sort "
                "what the question needs before returning it. E.g. pods[].{name:name,node:node} "
                "or length(pods). Preserve identities with relevant facts. Omit for full snapshot."
            ),
        }
    return {"type": "function", "function": {"name": "query_pod_lifecycle",
            "description": description, "parameters": {"type": "object", "properties": props,
                                                       "additionalProperties": False}}}


def replay(payload, arguments, mode):
    """Frozen-source adapter; no real kubectl, files or network available to the model."""
    if mode == "records":
        from scripts.evidence_record_trial import query_records

        return query_records(payload, arguments)
    allowed = {"namespace", "pod"} | ({"expression"} if mode == "compute" else set())
    if set(arguments) - allowed:
        return {"status": "error", "error": "unknown_arguments"}
    if any(not isinstance(value, str) for value in arguments.values()):
        return {"status": "error", "error": "arguments_must_be_strings"}
    if arguments.get("pod") and not arguments.get("namespace"):
        return {"status": "error", "error": "pod_requires_namespace"}
    if payload.get("status") != "success":
        return copy.deepcopy(payload)
    selected = copy.deepcopy(payload)
    selected["pods"] = [p for p in selected["pods"] if all(
        p.get(field) == arguments[arg] for arg, field in (("namespace", "namespace"), ("pod", "name"))
        if arguments.get(arg))]
    selected["returned_count"] = len(selected["pods"])
    # Preserve upstream scope/coverage; this is selection within a frozen page.
    if mode == "compute" and "expression" in arguments:
        return compute(selected, arguments["expression"])
    return selected


def oracle(payload):
    """Independent explicit traversal, not the candidate's expression engine."""
    reasons, nodes = [], {}
    for pod in payload["pods"]:
        node = pod.get("node")
        nodes[node] = nodes.get(node, 0) + 1
        for container in pod.get("containers", []):
            previous = container.get("last_state", {}).get("terminated", {})
            if previous.get("reason") == "OOMKilled":
                reasons.append({"namespace": pod["namespace"], "name": pod["name"],
                                "uid": pod["uid"], "phase": pod.get("phase"),
                                "container": container["name"], "ready": container.get("ready"),
                                "termination": previous,
                                "restart_count_total": container.get("restart_count_total"),
                                "restart_count_in_window": container.get("restart_count_in_window")})
    return {"previous_oom": reasons, "node_counts": nodes, "pod_count": len(payload["pods"]),
            "coverage": payload.get("coverage"), "history_complete": payload.get("history_complete")}


def evaluate(payload, question, mode, config, max_calls):
    from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
    from langchain_openai import ChatOpenAI
    from app.core.aicall.client import _parse_model
    from app.core.prompts import QUERY_COLLECT_PROMPT
    from app.core.workflow.query_contract import QueryAnswer
    from scripts.evaluate_evidence_view import validate_answer

    name, base = _parse_model(config["LLM_MODEL"], config["LLM_API_BASE"])
    model = ChatOpenAI(model=name, base_url=base, api_key=config["LLM_API_KEY"],
                       reasoning_effort=config.get("LLM_REASONING_EFFORT", "low"),
                       max_tokens=2500, timeout=60, max_retries=0)
    model = model.bind_tools([schema(mode), QueryAnswer])
    messages = [SystemMessage(content=QUERY_COLLECT_PROMPT), HumanMessage(content=question +
                "\n冻结证据实验：只回答这份快照，不代表当前实时环境，不可重新获取下一页。")]
    record = {"model_calls": 0, "model_seconds": [], "tools": [], "usage": {"input_tokens": 0, "output_tokens": 0},
              "answer": None, "answer_contract_valid": False, "execution_incomplete": None}
    start = time.monotonic()
    for _ in range(max_calls):
        record["model_calls"] += 1
        request_started = time.monotonic()
        try:
            response = model.invoke(messages)
        except Exception as exc:
            record["execution_incomplete"] = type(exc).__name__
            break
        finally:
            record["model_seconds"].append(time.monotonic() - request_started)
        messages.append(response)
        for key in record["usage"]:
            record["usage"][key] += (response.usage_metadata or {}).get(key, 0)
        if not response.tool_calls:
            record["answer"], record["answer_contract_valid"] = validate_answer(response.content)
            break
        for call in response.tool_calls:
            if call["name"] == "QueryAnswer":
                record["answer"], record["answer_contract_valid"] = validate_answer(call["args"])
                break
            tick = time.monotonic()
            output = (replay(payload, call["args"], mode) if call["name"] == "query_pod_lifecycle"
                      else {"status": "error", "error": "tool_unavailable_in_frozen_trial"})
            content = encode(output)
            record["tools"].append({"name": call["name"], "args": call["args"], "result": output,
                                    "bytes": len(content.encode()), "seconds": time.monotonic() - tick})
            messages.append(ToolMessage(content=content, tool_call_id=call["id"]))
        if record["answer"] is not None:
            break
    if record["answer"] is None and record["execution_incomplete"] is None:
        record["execution_incomplete"] = "step_limit"
    elif record["answer"] is not None and not record["answer_contract_valid"]:
        record["execution_incomplete"] = "invalid_answer_contract"
    record["seconds"] = time.monotonic() - start
    return record


def main():
    from scripts.evaluate_evidence_view import model_config

    parser = argparse.ArgumentParser(description=__doc__)
    source_options = parser.add_mutually_exclusive_group(required=True)
    source_options.add_argument("--source", type=Path)
    source_options.add_argument("--synthetic", choices=["complete", "partial", "empty", "error"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--max-calls", type=int, default=5)
    parser.add_argument("--cases", default="termination,count")
    parser.add_argument("--modes", default="raw,compute,records")
    args = parser.parse_args()
    questions = {
        "termination": "这份快照中哪些 Pod 的上一轮终止原因是 OOMKilled？列出 namespace、Pod、容器、当前状态、终止时间、退出码、累计重启数，并说明能否得知近10分钟重启次数。",
        "count": "这份快照有多少个 Pod？按节点统计数量。明确统计范围是否完整，不要逐个列出 Pod。",
        "explore": "检查这份快照里的 Pod，有哪些值得进一步关注？不要只看当前 Running/Ready，也考虑最近终止记录；列出对象、事实依据及信息不足之处。",
        "recovery": "从这份快照找出当前 ready=true、但上一轮终止为 OOMKilled 的容器；列出所属 Pod、容器、终止时间及重启计数，说明当前就绪能否排除最近发生过异常。",
        "cross_container": "这份快照里有没有同一个容器同时满足 ready=false 且上一轮终止原因为 OOMKilled？不要把一个 Pod 里不同容器的条件合并；说明未知字段和查询覆盖的限制。",
        "zeros": "lab-evidence 下 no-restarts 和 status-unknown 的 app 容器各累计重启多少次？区分零值、未知，以及能否确定近10分钟重启次数。",
    }
    cases = args.cases.split(",")
    modes = args.modes.split(",")
    if (not set(cases) <= questions.keys() or not 1 <= args.repeats <= 10 or not 1 <= args.max_calls <= 10
            or not set(modes) <= {"raw", "compute", "records"}):
        parser.error("invalid cases/repeats/max-calls")
    args.output.mkdir(parents=True, exist_ok=False)
    if args.synthetic:
        from scripts.evidence_boundary_fixtures import make_fixture

        payload_bytes = encode(make_fixture(args.synthetic)).encode()
        source_path = args.output / "synthetic-source.json"
        source_path.write_bytes(payload_bytes)
    else:
        source_path = args.source
        payload_bytes = source_path.read_bytes()
    payload = json.loads(payload_bytes)
    payload["raw_ref"] = str(source_path.resolve())
    config = model_config()
    manifest = {"model": config["LLM_MODEL"], "effort": config.get("LLM_REASONING_EFFORT", "low"),
                "jmespath": jmespath.__version__, "source": str(source_path),
                "source_sha256": hashlib.sha256(payload_bytes).hexdigest(), "oracle": oracle(payload),
                "origin": ("synthetic_input_live_model_pre_tool_trial" if args.synthetic
                           else "frozen_source_live_model_pre_tool_trial"), "serving_changes": False}
    manifest["synthetic_variant"] = args.synthetic
    manifest["max_model_calls"] = args.max_calls
    manifest["source_code_sha256"] = {}
    for filename in ("evaluate_evidence_computation.py", "evidence_record_trial.py", "evidence_boundary_fixtures.py"):
        implementation = Path(__file__).parent / filename
        content = implementation.read_bytes()
        manifest["source_code_sha256"][filename] = hashlib.sha256(content).hexdigest()
        (args.output / filename).write_bytes(content)
    (args.output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(encode({key: manifest[key] for key in ("model", "effort", "origin")}), flush=True)
    runs = [(case, repeat, mode) for case in cases for repeat in range(args.repeats)
            for mode in modes]
    random.Random(907).shuffle(runs)
    for case, repeat, mode in runs:
        try:
            result = evaluate(payload, questions[case], mode, config, args.max_calls)
        except Exception as exc:
            # Provider exception strings may contain request details; don't log them.
            result = {"execution_incomplete": type(exc).__name__}
        result.update(case=case, repeat=repeat, mode=mode)
        (args.output / f"{case}-{repeat}-{mode}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2))
        print(encode({key: value for key, value in result.items() if key not in {"tools", "answer"}}), flush=True)


if __name__ == "__main__":
    main()
