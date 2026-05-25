#!/usr/bin/env python3
"""Interactive remediation chat client.

The backend still exposes normal SSE/text streaming plus `/remediation/approve`.
This helper keeps the stream open and lets an operator type `approve` or
`reject` instead of copying curl commands.
"""

from __future__ import annotations

import argparse
import queue
import re
import sys
import threading
from typing import Dict, Optional
from urllib.parse import urlencode

import requests


APPROVAL_RE = re.compile(r"-d\s+run_id=(?P<run_id>\S+)\s+-d\s+approval_id=(?P<approval_id>\S+)")
APPROVE_WORDS = {"approve", "approved", "yes", "y"}
REJECT_WORDS = {"reject", "rejected", "no", "n"}


def parse_approval_hint(line: str) -> Optional[Dict[str, str]]:
    match = APPROVAL_RE.search(line or "")
    if not match:
        return None
    return {
        "run_id": match.group("run_id"),
        "approval_id": match.group("approval_id"),
    }


def _read_stdin(commands: "queue.Queue[str]") -> None:
    """Continuously read operator decisions while the response stream is open."""
    for line in sys.stdin:
        value = line.strip().lower()
        if value:
            commands.put(value)


def approval_prompt(kind: str = "approval", commands: Optional["queue.Queue[str]"] = None) -> bool:
    print(f"\n[{kind}] 输入 approve 同意，输入 reject 拒绝。", flush=True)
    while True:
        if commands is None:
            value = input(f"{kind} [approve/reject]: ").strip().lower()
        else:
            value = commands.get().strip().lower()
            print(f"[operator] {value}", flush=True)
        if value in APPROVE_WORDS:
            return True
        if value in REJECT_WORDS:
            return False
        print("请输入 approve 或 reject。", file=sys.stderr, flush=True)


def post_approval(base_url: str, run_id: str, approval_id: str, approved: bool, reviewer: str) -> None:
    response = requests.post(
        f"{base_url.rstrip('/')}/remediation/approve",
        data={
            "run_id": run_id,
            "approval_id": approval_id,
            "approved": "true" if approved else "false",
            "reviewer": reviewer,
        },
        timeout=30,
    )
    response.raise_for_status()
    print(f"\n[approval-posted] {response.text}\n", flush=True)


def stream_chat(base_url: str, question: str, reviewer: str) -> int:
    query = urlencode({"q": question, "stream": "true", "remediate": "true", "format": "text"})
    url = f"{base_url.rstrip('/')}/ask?{query}"
    commands: "queue.Queue[str]" = queue.Queue()
    if sys.stdin.isatty():
        threading.Thread(target=_read_stdin, args=(commands,), daemon=True).start()
    else:
        commands = None

    print("[terminal-approval] 使用本客户端启动时，可在审批中断后直接输入 approve 或 reject。", flush=True)
    with requests.get(url, stream=True, timeout=None) as response:
        response.raise_for_status()
        for raw_line in response.iter_lines(decode_unicode=True):
            if raw_line is None:
                continue
            print(raw_line, flush=True)
            hint = parse_approval_hint(raw_line)
            if hint:
                print(
                    "[approval-required] "
                    f"run_id={hint['run_id']} approval_id={hint['approval_id']}",
                    flush=True,
                )
                approved = approval_prompt("remediation", commands=commands)
                post_approval(base_url, hint["run_id"], hint["approval_id"], approved, reviewer)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AIOps diagnosis with interactive remediation approval.")
    parser.add_argument("question", help="诊断问题，例如：我的集群有什么问题")
    parser.add_argument("--url", default="http://10.2.0.48:30800", help="AIOps Copilot base URL")
    parser.add_argument("--reviewer", default="terminal", help="审批人标识")
    args = parser.parse_args()
    return stream_chat(args.url, args.question, args.reviewer)


if __name__ == "__main__":
    raise SystemExit(main())
