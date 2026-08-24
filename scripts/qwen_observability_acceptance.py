#!/usr/bin/env python3
"""Send production observability ToolMessages to the configured real Qwen model."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.context.observability_projection import project_observability_payload
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from jsonschema import ValidationError, validate


TOOL_BY_DIMENSION = {
    "metrics": "execute_pod_promql",
    "logging": "query_pod_logs",
    "tracing": "query_pod_tracing",
    "topology": "query_pod_topology",
}


def _load_tool_specs(mcp_repo: Path) -> list[dict[str, Any]]:
    sys.path.insert(0, str(mcp_repo.resolve()))
    from servers.holmes_tools.aiops_observability_query import TOOLS as OBS_TOOLS
    from servers.holmes_tools.kubernetes_core import TOOLS as K8S_TOOLS

    wanted_k8s = {
        "kubectl_describe",
        "kubectl_get_yaml",
        "kubectl_events",
        "kubectl_logs",
        "kubectl_previous_logs",
    }
    tools = list(OBS_TOOLS) + [tool for tool in K8S_TOOLS if tool.name in wanted_k8s]
    specs = [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            },
        }
        for tool in tools
    ]
    specs.append(
        {
            "type": "function",
            "function": {
                "name": "read_context_archive",
                "description": (
                    "Read a referenced context archive file in bounded pages when the "
                    "current observation is compressed or omitted evidence must be checked."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "archive_path": {"type": "string"},
                        "offset": {"type": "integer", "minimum": 0},
                        "length": {"type": "integer", "minimum": 200, "maximum": 40000},
                    },
                    "required": ["archive_path"],
                },
            },
        }
    )
    return specs


def _record_count(payload: dict[str, Any]) -> int:
    ledger = payload.get("fact_ledger") if isinstance(payload.get("fact_ledger"), dict) else {}
    return len(ledger.get("records") or payload.get("facts") or [])


def _select_payloads(case_dir: Path, namespace: str) -> list[tuple[Path, dict[str, Any]]]:
    best: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in sorted(case_dir.glob("*-evidence-*.raw.txt")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        entity = payload.get("entity") if isinstance(payload.get("entity"), dict) else {}
        dimension = str(payload.get("dimension") or "")
        if entity.get("namespace") != namespace or dimension not in TOOL_BY_DIMENSION:
            continue
        if str(payload.get("status") or "") != "query_succeeded":
            continue
        current = best.get(dimension)
        candidate_score = (
            _record_count(payload),
            1 if payload.get("coverage") == "present" else 0,
            path.name,
        )
        current_score = (
            _record_count(current[1]),
            1 if current[1].get("coverage") == "present" else 0,
            current[0].name,
        ) if current else (-1, -1, "")
        if candidate_score > current_score:
            best[dimension] = (path, payload)
    ordered = [best[key] for key in ("metrics", "logging", "tracing") if key in best]
    if not ordered:
        raise ValueError(f"no observability payloads found for {namespace} under {case_dir}")
    return ordered


def _tool_messages(
    selected: list[tuple[Path, dict[str, Any]]],
    max_chars: int,
) -> tuple[list[Any], list[dict[str, Any]]]:
    calls = []
    summaries = []
    tool_messages = []
    for index, (path, payload) in enumerate(selected, start=1):
        tool = TOOL_BY_DIMENSION[str(payload["dimension"])]
        call_id = f"observability-{index}"
        entity = payload.get("entity") or {}
        calls.append(
            {
                "name": tool,
                "args": {
                    "namespace": entity.get("namespace"),
                    "pod": entity.get("pod"),
                    "purpose": payload.get("purpose") or "inspect real evidence",
                },
                "id": call_id,
                "type": "tool_call",
            }
        )
        projected = project_observability_payload(
            payload,
            tool=tool,
            max_chars=max_chars,
            raw_ref=str(path.resolve()),
        )
        summary = json.loads(projected["summary"])
        summaries.append(summary)
        tool_messages.append(
            ToolMessage(
                content=projected["summary"],
                tool_call_id=call_id,
                name=tool,
                additional_kwargs={"aiops_raw_ref": str(path.resolve())},
            )
        )
    return [AIMessage(content="", tool_calls=calls), *tool_messages], summaries


def _extract_json(text: str) -> dict[str, Any]:
    value = text.strip()
    if value.startswith("```"):
        value = value.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("Qwen output is not a JSON object")
    return parsed


def _expected_visible_values(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    expected: dict[str, Any] = {
        "active_reason": None,
        "restart_value": None,
        "log_message": None,
        "allocated_mib": None,
        "http_codes": [],
    }
    for summary in summaries:
        for evidence in summary.get("evidence") or []:
            metric = str(evidence.get("metric") or "")
            labels = evidence.get("labels") if isinstance(evidence.get("labels"), dict) else {}
            if "last_terminated_reason" in metric and str(evidence.get("value")) not in {"0", "0.0"}:
                expected["active_reason"] = labels.get("reason")
            if "restarts_total" in metric:
                expected["restart_value"] = evidence.get("value")
            if evidence.get("message"):
                expected["log_message"] = evidence.get("message")
                attributes = evidence.get("attributes") if isinstance(evidence.get("attributes"), dict) else {}
                if attributes.get("allocated_mib") is not None:
                    expected["allocated_mib"] = attributes["allocated_mib"]
                if evidence.get("http_status") is not None:
                    expected["http_codes"].append(evidence["http_status"])
            data = evidence.get("data") if isinstance(evidence.get("data"), dict) else {}
            if data.get("response_code") is not None:
                expected["http_codes"].append(data["response_code"])
    expected["http_codes"] = sorted(set(expected["http_codes"]))
    return expected


def run(args: argparse.Namespace) -> dict[str, Any]:
    api_key = os.environ.get("QWEN_AUDIT_API_KEY", "").strip()
    if not api_key:
        raise ValueError("QWEN_AUDIT_API_KEY is required")
    tool_specs = _load_tool_specs(Path(args.mcp_repo))
    registered_names = {
        spec["function"]["name"]
        for spec in tool_specs
    }
    selected = _select_payloads(Path(args.case_dir), args.namespace)
    observation_messages, summaries = _tool_messages(selected, args.max_chars)
    entity = summaries[0].get("entity") or {}
    base_messages = [
        SystemMessage(
            content=(
                "你是 AIOps evidence Agent。只能使用 ToolMessage 中可见的证据；"
                "不得把缺失字段补成事实，不得发明工具。summary 是有损工作视图，"
                "coverage/truncation/summary_selection/retrieval 决定是否需要回查。"
            )
        ),
        HumanMessage(
            content=(
                f"检查 {entity.get('namespace')}/{entity.get('pod')}。"
                "以下是刚完成的真实工具调用结果。"
            )
        ),
        *observation_messages,
    ]
    messages = [
        *base_messages,
        HumanMessage(
            content=(
                "不要调用工具。只输出一个 JSON 对象，不要 Markdown。格式："
                '{"confirmed_facts":[{"fact":"必须保留原始字段名和精确值","evidence_id":"fact id"}],'
                '"information_gaps":["..."],'
                '"compression_awareness":{"is_lossy_working_view":true,"why":"...","raw_ref_available":true},'
                '"next_action":{"tool":null或已注册工具名,"reason":"..."}}。'
                "必须同时检查正常 HTTP 200、零值和 trend_evaluable=false 是否有诊断价值。"
            )
        ),
    ]
    model = ChatOpenAI(
        model=args.model,
        api_key=api_key,
        base_url=args.api_base,
        temperature=0,
        max_tokens=1400,
        streaming=False,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    # The comprehension turn must see the same registered tool schemas as the
    # real Agent even though it is asked not to execute one in this turn.
    # Otherwise a free-text next_action name cannot be evaluated fairly.
    response = model.bind_tools(tool_specs, tool_choice="none").invoke(messages)
    parsed = _extract_json(str(response.content))
    rendered = json.dumps(parsed, ensure_ascii=False)
    expected = _expected_visible_values(summaries)
    next_tool = ((parsed.get("next_action") or {}).get("tool"))
    checks = {
        "json_object": True,
        "active_reason_recalled": (
            expected["active_reason"] is None
            or str(expected["active_reason"]) in rendered
        ),
        "restart_value_recalled": (
            expected["restart_value"] is None
            or str(expected["restart_value"]) in rendered
        ),
        "log_message_recalled": (
            expected["log_message"] is None
            or str(expected["log_message"]) in rendered
        ),
        "allocated_mib_recalled": (
            expected["allocated_mib"] is None
            or str(expected["allocated_mib"]) in rendered
        ),
        "http_codes_recalled": all(str(code) in rendered for code in expected["http_codes"]),
        "compression_understood": bool(
            (parsed.get("compression_awareness") or {}).get("is_lossy_working_view")
        ),
        "raw_ref_understood": bool(
            (parsed.get("compression_awareness") or {}).get("raw_ref_available")
        ),
        "next_tool_registered": next_tool in (None, "") or next_tool in registered_names,
        "no_known_invented_tool": "get_evidence_detail" not in rendered,
    }
    tool_decision: dict[str, Any] | None = None
    if args.exercise_tool_call:
        decision_response = model.bind_tools(tool_specs).invoke(
            [
                *base_messages,
                HumanMessage(
                    content=(
                        "当前可见证据不足以完成下面的诊断目标。你必须现在通过 function calling "
                        "调用一个且仅一个已注册工具；不要只用文字描述，也不要发明工具。"
                        f"诊断目标：{args.decision_goal}"
                    )
                ),
            ]
        )
        calls = list(decision_response.tool_calls or [])
        call = calls[0] if len(calls) == 1 else {}
        tool_name = str(call.get("name") or "")
        tool_args = call.get("args") if isinstance(call.get("args"), dict) else {}
        schema_valid = False
        schema_error = None
        schema = next(
            (
                item["function"]["parameters"]
                for item in tool_specs
                if item["function"]["name"] == tool_name
            ),
            None,
        )
        if schema is not None:
            try:
                validate(instance=tool_args, schema=schema)
                schema_valid = True
            except ValidationError as exc:
                schema_error = exc.message
        tool_decision = {
            "call_count": len(calls),
            "tool": tool_name or None,
            "args": tool_args,
            "registered": tool_name in registered_names,
            "schema_valid": schema_valid,
            "schema_error": schema_error,
            "content": str(decision_response.content or ""),
            "usage_metadata": decision_response.usage_metadata,
        }
        checks.update(
            {
                "function_call_exactly_one": len(calls) == 1,
                "function_call_registered": tool_name in registered_names,
                "function_call_schema_valid": schema_valid,
                "function_call_not_invented": tool_name != "get_evidence_detail",
            }
        )
    report = {
        "model": args.model,
        "namespace": args.namespace,
        "toolmessages": [
            {
                "tool": TOOL_BY_DIMENSION[payload["dimension"]],
                "raw_path": str(path),
                "summary_chars": len(json.dumps(summary, ensure_ascii=False, separators=(",", ":"))),
                "evidence_selected": (summary.get("summary_selection") or {}).get("selected"),
                "evidence_omitted": (summary.get("summary_selection") or {}).get("omitted"),
                "coverage": summary.get("coverage"),
                "truncated": (summary.get("truncation") or {}).get("truncated"),
            }
            for (path, payload), summary in zip(selected, summaries)
        ],
        "expected_visible_values": expected,
        "qwen_response": parsed,
        "checks": checks,
        "passed": all(checks.values()),
        "usage_metadata": response.usage_metadata,
    }
    if tool_decision is not None:
        report["tool_decision"] = tool_decision
        report["passed"] = all(checks.values())
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--case-dir", required=True)
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--mcp-repo", required=True)
    parser.add_argument("--max-chars", type=int, default=3000)
    parser.add_argument("--exercise-tool-call", action="store_true")
    parser.add_argument("--decision-goal", default="补齐当前根因证据缺口")
    args = parser.parse_args()
    report = run(args)
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
