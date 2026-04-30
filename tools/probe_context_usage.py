#!/usr/bin/env python3
"""Probe server-side prompt token usage for representative workflow messages.

This does not diagnose the cluster. It sends minimal `max_tokens=1` requests to
the configured OpenAI-compatible model endpoint and prints exact
`usage.prompt_tokens` values returned by the gateway.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.context.usage_probe import OpenAIUsageProbe
from app.core.prompts import get_workflow_prompt


def _messages(system_prompt: str, user_message: str):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe exact prompt tokens via chat completion usage.")
    parser.add_argument("--model", default=os.getenv("LLM_MODEL", "openai/Qwen3-32B-AWQ"))
    parser.add_argument("--api-base", default=os.getenv("LLM_API_BASE", "http://10.2.0.54:4000/v1"))
    parser.add_argument("--api-key", default=os.getenv("LLM_API_KEY", ""))
    parser.add_argument("--question", default="namespace=xnet pod=ham-wcc79 为什么 ImagePullBackOff？")
    parser.add_argument("--context-window", type=int, default=int(os.getenv("MODEL_CONTEXT_WINDOW", "0") or 0))
    args = parser.parse_args()

    probe = OpenAIUsageProbe(api_base=args.api_base, api_key=args.api_key)
    model_name = args.model.split("/", 1)[-1]

    layer_system = get_workflow_prompt("layer", prompt_language="zh")
    evidence_system = get_workflow_prompt("evidence", prompt_language="zh")
    rca_system = get_workflow_prompt("rca", prompt_language="zh")
    conclusion_system = get_workflow_prompt("conclusion", prompt_language="zh")

    layer_user = args.question
    evidence_user = "\n".join([
        f"用户问题: {args.question}",
        "上游定位: pod_abnormal_type=ImagePullFailed, primary_pod=ham-wcc79, namespace=xnet",
        "要求: 先输出 evidence_plan JSON，再调用必要工具采集证据。",
    ])
    rca_user = "\n".join([
        f"用户问题: {args.question}",
        "证据摘要: Pod ham-wcc79 ImagePullBackOff; describe events include Failed to pull image; pod yaml has image xnet.registry.io:8443/ham/ham:v2.24.",
    ])
    conclusion_user = "\n".join([
        f"用户问题: {args.question}",
        "根因: 镜像拉取失败，需依据 evidence 和 RCA 生成用户报告。",
    ])

    evidence_after_tools = "\n\n".join([
        evidence_user,
        "已采集工具结果:",
        "1. kubectl_describe: Pod ham-wcc79 status=ImagePullBackOff; Events include Back-off pulling image.",
        "2. kubectl_get_yaml: image=xnet.registry.io:8443/ham/ham:v2.24; imagePullSecrets missing.",
        "3. kubectl_get_by_kind_in_namespace Secret: xnet-bmcs exists but type=Opaque.",
        "4. kubectl_get_by_kind_in_namespace Pod: only ham-wcc79 is ImagePullBackOff in namespace xnet.",
    ])
    rca_after_evidence = "\n\n".join([
        rca_user,
        "evidence_items=4/5; missing=e5 kubelet log optional; early_stop=critical and important evidence satisfied.",
        "tool_data includes describe/yaml/secrets/pod table summaries.",
    ])
    conclusion_after_rca = "\n\n".join([
        conclusion_user,
        "evidence_summary: 4/5 collected, ImagePullBackOff confirmed, imagePullSecrets likely missing or invalid.",
        "rca_summary: root cause confidence=90%, image pull authentication/registry access issue.",
    ])

    cases = [
        ("layer.before", layer_system, layer_user),
        ("evidence.before", evidence_system, evidence_user),
        ("evidence.after_tools", evidence_system, evidence_after_tools),
        ("rca.before", rca_system, rca_user),
        ("rca.after_evidence", rca_system, rca_after_evidence),
        ("conclusion.before", conclusion_system, conclusion_user),
        ("conclusion.after_rca", conclusion_system, conclusion_after_rca),
    ]

    output = {
        "model": model_name,
        "api_base": args.api_base,
        "context_window": args.context_window or None,
        "cases": [],
    }
    for node, system, user in cases:
        result = probe.count_prompt_tokens(model_name, _messages(system, user))
        item = {
            "node": node,
            "prompt_tokens": result.prompt_tokens,
            "accuracy": result.accuracy,
            "source": result.source,
            "error": result.error or None,
        }
        if args.context_window and result.prompt_tokens is not None:
            item["input_usage"] = round(result.prompt_tokens / args.context_window, 4)
        output["cases"].append(item)

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
