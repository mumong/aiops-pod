# Quickstart: Remediation Approval And Think Stream

## Automated Verification

Run focused tests for the changed surfaces:

```bash
pytest tests/unit/api/test_query_routes.py \
  tests/unit/workflow/test_remediation_plan_handling.py \
  tests/unit/remediation/test_plans.py \
  tests/unit/remediation/test_agent.py \
  tests/unit/remediation/test_executor.py \
  tests/unit/test_service_think_stream.py \
  tests/unit/aicall/test_event_loop_safety.py -q
```

Run compile/import smoke checks for edited modules:

```bash
python3 -m py_compile \
  app/api/routes.py \
  app/core/workflow/executor.py \
  app/core/workflow/nodes/base.py \
  app/core/workflow/nodes/conclusion_formatter.py \
  app/core/remediation/*.py \
  app/core/service.py \
  app/core/aicall/client.py
```

## Real Deployment Validation

Use the repository deployment path requested by the user:

```bash
make delete
make build
make push
make deploy
```

Wait for rollout and health:

```bash
kubectl rollout status deployment/aiops-copilot -n aiops --timeout=300s
curl -sS http://10.2.0.49:30800/health
```

## Review Mode Validation

Set runtime config to:

```yaml
workflow:
  remediation:
    enabled: true
    mode: review
```

Run an ordinary `/ask` request without `remediate=true`:

```bash
curl --no-buffer \
  -H "Accept: text/event-stream" \
  -G "http://10.2.0.49:30800/ask" \
  --data-urlencode "q=我的集群有什么问题？" \
  --data-urlencode "stream=true" \
  --data-urlencode "format=text"
```

Expected:
- Diagnosis completes.
- Structured plan contains a finalizer patch action for the confirmed TerminatingStuck case.
- Stream emits `remediation_approval_required`.
- No write command runs before approval.
- If the structured plan is missing or inconsistent, stream emits `invalid_plan` with a clear reason.

## Auto Mode Validation

In a controlled e2e environment only, set:

```yaml
workflow:
  remediation:
    enabled: true
    mode: auto
```

Run the same ordinary `/ask` request. Expected:
- No blocking approval prompt.
- Safe validated patch action executes.
- Verification observes the Pod is deleted, NotFound, or no longer stuck.

## Think Stream Validation

Run a streaming query:

```bash
curl --no-buffer \
  -G "http://10.2.0.49:30800/query" \
  --data-urlencode "q=查询 up 指标" \
  --data-urlencode "stream=true" \
  --data-urlencode "format=text" \
  --data-urlencode "max_steps=8"
```

Expected:
- Output shows LLM intermediate reasoning when the provider exposes it.
- Output shows tool start/result and heartbeat/progress state.
- Missing literal `<think>` tags is acceptable only if provider reasoning is unavailable and progress events remain visible.

## Validation Record - 2026-05-29

Automated verification:

```text
PYTHONPATH=. .venv/bin/pytest tests/unit/api/test_query_routes.py tests/unit/workflow/test_remediation_plan_handling.py tests/unit/remediation/test_plans.py tests/unit/remediation/test_agent.py tests/unit/remediation/test_executor.py tests/unit/test_service_think_stream.py tests/unit/aicall/test_event_loop_safety.py -q
73 passed, 15 warnings

PYTHONPATH=. .venv/bin/python -m py_compile app/api/routes.py app/core/workflow/executor.py app/core/workflow/nodes/base.py app/core/workflow/nodes/conclusion_formatter.py app/core/remediation/agent.py app/core/remediation/approval.py app/core/remediation/executor.py app/core/remediation/models.py app/core/remediation/plans.py app/core/service.py app/core/aicall/client.py
passed
```

Deployment verification:

```text
VERSION=11.0.1
make delete
make build
make push
make deploy
kubectl rollout status deployment/aiops-copilot -n aiops --timeout=300s
deployment "aiops-copilot" successfully rolled out
image: xnet.registry.io:8443/xnet-cloud/aiops-copilot:11.0.1
health: {"status":"healthy","config_loaded":true,"ai_initialized":true,"mode":"AICall(LangGraph)","model":"openai/Qwen3.6-35B-A3B"}
```

Review-mode `/ask` without `remediate`:

```text
run_id=1326da88687c4106
output contained: 🛠️ 修复审批中断
approval_kind=plan
approval_id=ba4dbf7558f1
report: /tmp/aiops/reports/L1-我的集群有什么问题？重点检查 aiops-e2e names_20260529_085026.md
structured plan: remediation_available=true, fix_type=remove_finalizer
action: kubectl patch pod terminating-stuck -n aiops-e2e -p '{"metadata":{"finalizers":null}}' --type=merge
pre-approval safety check: Pod remains Terminating and finalizers remain ["aiops.e2e/hold"]
```

Think/progress stream:

```text
/query q=查询 up 指标
output contained AI intermediate text, tool_start for fetch_runbook, and tool_result success.
```
