# Quickstart: Ask Conclusion Remediation JSON

## Focused Unit Validation

```bash
pytest tests/unit/workflow/test_ask_conclusion_remediation_json.py \
  tests/unit/workflow/test_remediation_plan_handling.py \
  tests/unit/workflow/test_query_direct_mode.py
```

Expected:
- Confirmed finalizer case yields a parseable `remove_finalizer` action.
- Unsafe or ambiguous cases do not synthesize write actions.
- Query direct tests remain green.

## Near-real Workflow Validation

Run an `/ask` case that produces current Pod evidence:

```bash
curl -N "http://127.0.0.1:8000/ask?q=我的集群有什么问题？&format=sse&stream=true"
```

Expected:
- Final report includes `## 🧩 结构化修复计划`.
- For confirmed TerminatingStuck finalizer evidence, `extract_remediation_plan` parses `remediation_available=true`.
- With `workflow.remediation.enabled=true` and `mode=review`, stream can reach `remediation_approval_required`.

## Deployment Validation

If validating in the cluster, follow the project release flow:

```bash
make delete
make build
make push
make deploy
kubectl rollout status deployment/aiops-copilot -n aiops
```

Then run the `/ask` query and inspect streamed output plus context archives.
