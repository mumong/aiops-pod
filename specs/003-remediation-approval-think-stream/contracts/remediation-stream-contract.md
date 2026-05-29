# Contract: Remediation And Think Stream

## Configuration Contract

```yaml
workflow:
  remediation:
    enabled: true
    mode: review   # review | auto
    executor: react
```

Rules:
- `enabled=false` disables post-diagnosis remediation.
- `mode=review` evaluates the structured plan and requires human approval before plan acceptance and each write command.
- `mode=auto` evaluates the structured plan and automatically approves safe actions.
- `AUTO_REMEDIATE` is not part of the contract.
- `/ask` does not require `remediate=true` to enter remediation when workflow config enables it.

## Structured Plan Contract

```json
{
  "remediation_available": true,
  "fix_type": "single_issue",
  "risk_level": "medium",
  "requires_human_approval": true,
  "issue_groups": [
    {
      "group_id": "g1",
      "problem_type": "TerminatingStuck",
      "target": "pod/terminating-stuck",
      "auto_fixable": true
    }
  ],
  "basis": [
    "current pod yaml shows deletionTimestamp",
    "current pod yaml shows metadata.finalizers is non-empty"
  ],
  "actions": [
    {
      "id": "remove-finalizer-g1",
      "type": "kubectl",
      "description": "Remove confirmed blocking finalizer from the stuck pod",
      "risk": "medium",
      "dry_run_command": "kubectl get pod terminating-stuck -n aiops-e2e -o yaml",
      "execute_command": "kubectl patch pod terminating-stuck -n aiops-e2e -p '{\"metadata\":{\"finalizers\":null}}' --type=merge",
      "verify_command": "kubectl get pod terminating-stuck -n aiops-e2e",
      "metadata": {
        "group_id": "g1",
        "namespace": "aiops-e2e",
        "name": "terminating-stuck",
        "expected_verify": "NotFound or object no longer Terminating"
      }
    }
  ],
  "stop_conditions": [
    "current pod no longer exists before execution",
    "finalizers are already empty",
    "operator rejects the plan or action"
  ]
}
```

Invalid plan behavior:
- If a confirmed repairable case has natural-language write advice but no structured action, emit `remediation_finished` with `status=invalid_plan`.
- Do not extract commands from prose to repair the plan.

## Stream Event Contract

### Approval Required

```json
{
  "type": "remediation_approval_required",
  "run_id": "abc123",
  "approval_id": "approval123",
  "approval_kind": "plan",
  "title": "是否认可诊断报告中的修复方案",
  "payload": {
    "mode": "review",
    "actions": []
  }
}
```

### Invalid Plan

```json
{
  "type": "remediation_finished",
  "run_id": "abc123",
  "status": "invalid_plan",
  "reason": "confirmed repairable issue has natural-language remediation but no structured actions"
}
```

### Think / Progress

```json
{
  "type": "thinking",
  "node": "evidence",
  "node_name": "证据链采集",
  "thinking_type": "ai_message",
  "content": "<think>model provided reasoning</think> Next I will fetch pod yaml.",
  "iteration": 1
}
```

Rules:
- `full` mode should show available LLM reasoning and progress.
- `truncated` mode should preserve progress and truncate only raw reasoning.
- `hidden` mode should hide raw reasoning and keep tool/progress/approval state visible.
