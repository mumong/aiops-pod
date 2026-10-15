"""Opt-in real-model, read-only planner replay; no jobs, approvals or execution."""

import argparse
import ast
import json
import threading
import uuid
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expect-actions", action="store_true")
    parser.add_argument(
        "--replay-tools", type=Path, help="Frozen historical evidence; not a live cluster test"
    )
    args = parser.parse_args()
    from app.core.remediation.executor import RemediationExecutor
    from app.core.remediation.pod_executor import PodRepairExecutor
    from app.core.service import get_service
    from app.core.workflow.nodes import remediation

    def forbidden(*a, **kw):
        raise AssertionError("Planner test must never execute repairs")

    PodRepairExecutor.run = forbidden
    RemediationExecutor.run = forbidden
    source = args.prompt_file.read_text()
    if args.prompt_file.suffix == ".py":
        source = next(
            ast.literal_eval(n.value)
            for n in ast.parse(source).body
            if isinstance(n, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id == "POD_REMEDIATION_PROMPT" for t in n.targets
            )
        )
    remediation.POD_REMEDIATION_PROMPT = source
    material = json.loads(args.input.read_text())
    if args.replay_tools:
        material["repair_context"]["verification_replay_evidence"] = {
            "note": "离线快照评测：以下为该次规划时真实工具返回；只评价在该快照及本次用户反馈下的方案，不推断现在状态，不执行。",
            "results": [
                {"source": str(p), "result": p.read_text()}
                for p in sorted(args.replay_tools.glob("*.raw.txt"))
            ],
        }
    service = get_service()
    service.initialize()
    node = remediation.RemediationNode(service, runbook_catalog=service.merged_catalog)
    node.ai_call = service._build_request_scoped_ai_call()
    node.tools = service.mcp_tools or []
    node.cancel_event = threading.Event()
    node.current_run_id = "verify-feedback-" + uuid.uuid4().hex[:16]
    if args.replay_tools:
        node.tools = []
        call = node._call_llm

        def replay_call(question, prompt, **kw):
            kw["force_no_tools"] = True
            # Freeze evaluation time, not the planning decision: otherwise the
            # model reasonably requests today's resources for an old archive.
            prompt += (
                "\n评测执行环境：本次是历史时点回放，任务是生成原输入对应时点的方案，不是今天的方案。"
                "verification_replay_evidence.results 是该时点真实工具结果，视为该时点的观测；"
                "没有工具可调用，不要求今天的现场状态。是否能生成动作仍按上述规则与证据自主判断。"
            )
            return call(question, prompt, **kw)

        node._call_llm = replay_call
    result = node.execute(material)
    args.output.write_text(json.dumps(result, ensure_ascii=False, default=str))
    draft = result["remediation_draft"]
    assert not draft.get("planning_error"), draft.get("planning_error")
    group = material["current_repair_group"]["group_id"]
    assert all(a["group_id"] == group for a in draft["actions"])
    if args.expect_actions:
        assert draft["actions"], "No actions; inspect output and current resources"
    print(
        json.dumps(
            {
                "run_id": node.current_run_id,
                "group": group,
                "actions": len(draft["actions"]),
                "executed": False,
                "historical_replay": bool(args.replay_tools),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
