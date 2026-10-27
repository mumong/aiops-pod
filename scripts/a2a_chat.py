#!/usr/bin/env python3
"""Chat with the AIOps A2A agent from a terminal, the way another agent would (stdlib only).

    python3 scripts/a2a_chat.py                         # this node: http://127.0.0.1:30801
    python3 scripts/a2a_chat.py http://10.2.5.85:30801  # another cluster
    python3 scripts/a2a_chat.py -q "各节点 CPU 和内存使用率怎么样？"   # one question, then exit

Ask anything; progress streams while the agent works. When it pauses (input-required):
  approvals  -> y = approve all listed, n = reject all, or "批准 <id>" / "拒绝 <id>"
  a question -> type the answer (e.g. "所有边缘集群")
/new starts a new conversation; exit (or Ctrl-D) quits.
"""

import argparse
import json
import sys
import urllib.request
import uuid

TERMINAL = {"completed", "failed", "canceled", "rejected"}


def card(url):
    with urllib.request.urlopen(url + ".well-known/agent-card.json", timeout=15) as resp:
        data = json.loads(resp.read())
    skills = ", ".join(s["id"] for s in data.get("skills", []))
    print(f"已连接 {data.get('name')} {data.get('version')}  技能：{skills}")


def text_of(parts):
    return "\n".join(p.get("text", "") for p in parts or [] if p.get("kind") == "text").strip()


def approvals_of(parts):
    for p in parts or []:
        if p.get("kind") == "data" and isinstance(p.get("data"), dict):
            return p["data"].get("approvals") or []
    return []


def send(url, text, task_id=None, context_id=None):
    """message/stream; prints progress; returns (state, task_id, context_id, status_parts)."""
    message = {
        "kind": "message",
        "role": "user",
        "messageId": uuid.uuid4().hex,
        "parts": [{"kind": "text", "text": text}],
    }
    if task_id:
        message["taskId"] = task_id
    if context_id:
        message["contextId"] = context_id
    body = {
        "jsonrpc": "2.0",
        "id": uuid.uuid4().hex,
        "method": "message/stream",
        "params": {"message": message},
    }
    req = urllib.request.Request(
        url,
        json.dumps(body).encode(),
        {"Content-Type": "application/json", "Accept": "text/event-stream"},
    )
    state, parts, last = None, [], ""
    with urllib.request.urlopen(req, timeout=3600) as resp:
        for raw in resp:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            event = json.loads(line[5:])
            if event.get("error"):
                print("错误：", json.dumps(event["error"], ensure_ascii=False))
                return "failed", task_id, context_id, []
            result = event.get("result") or {}
            task_id = result.get("taskId") or (
                result.get("id") if result.get("kind") == "task" else task_id
            )
            context_id = result.get("contextId") or context_id
            if result.get("kind") == "artifact-update":
                report = text_of((result.get("artifact") or {}).get("parts"))
                if report:
                    print("\n" + "─" * 60 + "\n" + report + "\n" + "─" * 60)
                continue
            status = result.get("status") or {}
            if not status:
                continue
            state = status.get("state") or state
            parts = (status.get("message") or {}).get("parts") or []
            note = text_of(parts)
            if state == "working" and note and note != last:
                print(f"  … {note.splitlines()[0][:150]}")
                last = note
            if state in TERMINAL or state == "input-required":
                break
    return state, task_id, context_id, parts


def reply_for(answer, approvals):
    """y / n map to a decision for every listed approval; anything else is sent as typed."""
    word = answer.strip().lower()
    if approvals and word in {"y", "yes", "批准", "全部批准", "同意"}:
        return "\n".join(f"批准 {a['approval_id']}" for a in approvals)
    if approvals and word in {"n", "no", "拒绝", "全部拒绝"}:
        return "\n".join(f"拒绝 {a['approval_id']}" for a in approvals)
    return answer


def ask(url, question, context_id, read_line):
    state, task_id, context_id, parts = send(url, question, context_id=context_id)
    while state == "input-required":
        approvals = approvals_of(parts)
        if approvals:
            print("\n需要审批（输入 y 全部批准 / n 全部拒绝）：")
            for a in approvals:
                where = f" [集群 {a['cluster']}]" if a.get("cluster") else ""
                print(
                    f"  · {a.get('description')}{where}\n    命令：{a.get('execute_command')}\n"
                    f"    风险：{a.get('risk')}   approval_id={a['approval_id']}"
                )
        else:
            print("\n" + (text_of(parts) or "对方需要补充信息："))
        answer = read_line("回复> ")
        if answer is None:
            return context_id
        state, task_id, context_id, parts = send(
            url, reply_for(answer, approvals), task_id, context_id
        )
    if state and state != "completed":
        print(f"\n[{state}] {text_of(parts)}")
    elif state == "completed" and text_of(parts):
        print(f"\n✔ {text_of(parts)}")
    return context_id


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("url", nargs="?", default="http://127.0.0.1:30801")
    ap.add_argument("-q", "--question", help="ask one question and exit")
    args = ap.parse_args()
    url = args.url.rstrip("/") + "/"

    def read_line(prompt):
        try:
            return input(prompt)
        except EOFError:
            return None

    card(url)
    if args.question:
        ask(url, args.question, None, read_line)
        return
    print("直接输入问题；/new 新对话；exit 退出\n")
    context_id = None
    while True:
        question = read_line("\n你> ")
        if question is None or question.strip() in {"exit", "quit"}:
            break
        if question.strip() == "/new":
            context_id = None
            print("已开始新对话")
            continue
        if question.strip():
            context_id = ask(url, question.strip(), context_id, read_line)


if __name__ == "__main__":
    sys.exit(main())
