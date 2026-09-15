# Deterministic Pod Health and Event Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make current Pod state and a 30-minute restart window authoritative for HEALTHY routing, while limiting Kubernetes Event collection by abnormal type and to one attempt per Pod.

**Architecture:** Extend the existing ObservationProcessor fact boundary with explicit scan metadata, then reconcile Layer output deterministically in `LayerClassifierNode` before graph routing. Filter Event plan items from the structured handoff and use a canonical, shareable AICall execution cache so repeated Event calls for one Pod are served from the first result, including empty/error results.

**Tech Stack:** Python 3, Pydantic v2, LangGraph, LangChain agent middleware, pytest, YAML configuration.

---

## File map

- `app/core/context/observation.py`: parse Pod tables and emit the authoritative 30-minute restart/scan facts.
- `app/core/workflow/schemas.py`: preserve scan facts across the typed Layer handoff boundary.
- `app/core/workflow/nodes/layer_classifier.py`: replace one-way HEALTHY protection with two-way deterministic Pod health reconciliation.
- `app/core/workflow/nodes/conclusion_formatter.py`: render HEALTHY from structured facts without LLM or historical tool noise.
- `app/core/workflow/nodes/evidence_collector.py`: apply the abnormal-type Event matrix and share Event deduplication state across evidence rounds.
- `app/core/aicall/client.py`: canonicalize Event execution keys and cache the first Event attempt, including empty/error results.
- `app/core/workflow/nodes/base.py`: forward an optional shared tool execution cache into AICall.
- `app/core/prompts.py`: align agent instructions with conditional Event collection and independent K8s/Elastic log dimensions.
- `deploy/configmap/config.yaml`: document/default the 30-minute health window and Event policy.
- `README.md`: document the product behavior.
- Tests under `tests/unit/aicall/` and `tests/unit/workflow/`: lock all deterministic behavior.

### Task 1: Make the restart window and scan contract explicit

**Files:**
- Modify: `tests/unit/aicall/test_observation_processing.py`
- Modify: `app/core/context/observation.py`

- [ ] **Step 1: Write failing boundary tests**

Add tests that process Running/Ready Pod tables at 29m59s, 30m, 30m01s, old cumulative restarts, and positive restart counts without an age. Assert that only ages at or below 30 minutes enter `recent_restart_rows`, and assert:

```python
assert structured["scan_confirmed"] is True
assert structured["restart_window_seconds"] == 1800
assert structured["row_count"] == expected_rows
```

- [ ] **Step 2: Run the focused tests and verify failure**

Run:

```bash
pytest -q tests/unit/aicall/test_observation_processing.py -k 'recent_restart or restart_window'
```

Expected: the 29m59s/30m cases fail because the current window is 900 seconds, and scan metadata keys are absent.

- [ ] **Step 3: Implement the 30-minute fact contract**

Change the constant and structured result:

```python
class ObservationProcessor:
    RECENT_RESTART_WINDOW_SECONDS = 30 * 60

# in _extract_table
structured = {
    "status": "table_summarized",
    "scan_confirmed": bool(re.search(r"\bREADY\b.*\bSTATUS\b", header)),
    "row_count": max(0, len(lines) - 1),
    "abnormal_count": len(abnormal),
    "recent_restart_count": len(recent_restart_rows),
    "recent_restart_rows": recent_restart_rows,
    "restart_window_seconds": self.RECENT_RESTART_WINDOW_SECONDS,
    "status_counts": status_counts,
    "header": header,
    "selected_rows": selected,
}
```

Do not infer recency from a bare cumulative count.

- [ ] **Step 4: Run the focused tests**

Run the command from Step 2. Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/core/context/observation.py tests/unit/aicall/test_observation_processing.py
git commit -m "fix: use 30 minute pod restart window"
```

### Task 2: Reconcile Layer output from current Pod facts

**Files:**
- Modify: `tests/unit/workflow/test_context_handoff.py`
- Modify: `app/core/workflow/schemas.py`
- Modify: `app/core/workflow/nodes/layer_classifier.py`

- [ ] **Step 1: Write failing reconciliation tests**

Add tests for these cases:

```python
def test_layer_guard_forces_healthy_when_confirmed_scan_has_no_abnormal_pods():
    # LLM says ABNORMAL/HighRestarts and invents three abnormal Pods.
    # Successful Pod table has abnormal_count=0 and recent_restart_count=0.
    # Expect Layer.HEALTHY and empty abnormal_pods/issue_groups.

def test_layer_guard_does_not_force_healthy_without_confirmed_scan():
    # No successful Pod table event. Preserve the LLM ABNORMAL result.

def test_layer_guard_keeps_running_notready_abnormal():
    # Running 0/1 is selected by the scan. Expect ABNORMAL/NotReady.
```

Also extend handoff serialization assertions for `scan_confirmed`, `row_count`, `abnormal_count`, `recent_restart_count`, and `restart_window_seconds`.

- [ ] **Step 2: Run tests and verify the HighRestarts test fails**

```bash
pytest -q tests/unit/workflow/test_context_handoff.py -k 'layer_guard or abnormal_summary'
```

Expected: the new ABNORMAL-to-HEALTHY case fails.

- [ ] **Step 3: Extend the typed handoff schema**

Add these fields to `CurrentAbnormalSummary`:

```python
scan_confirmed: bool = False
row_count: int = 0
abnormal_count: int = 0
recent_restart_count: int = 0
restart_window_seconds: int = 1800
```

- [ ] **Step 4: Make current scan Pods authoritative**

In `_extract_current_abnormal_summary_from_events`, copy the five scan fields from the structured tool result. The default result must set `scan_confirmed=False`.

In `_build_layer_handoff`, use exact replacement when the scan is confirmed:

```python
if current_abnormal_summary.get("scan_confirmed"):
    abnormal_pods = list(current_abnormal_pods)
elif current_abnormal_pods:
    abnormal_pods = self._merge_current_abnormal_pods(
        abnormal_pods,
        current_abnormal_pods,
    )
```

This clears stale LLM-only Pods when a successful scan finds zero abnormalities.

- [ ] **Step 5: Extend the guard into two-way reconciliation**

Keep the existing private method name for compatibility, but apply this order:

```python
if layer == Layer.QUERY:
    return layer, layers
summary = layer_handoff.get("current_abnormal_summary") or {}
if not summary.get("scan_confirmed"):
    return layer, layers
if self._handoff_has_active_abnormalities(layer_handoff):
    target = Layer.ABNORMAL
else:
    target = Layer.HEALTHY
```

Update `layer_result`, `layer_handoff`, confidence, reasoning, `abnormal_pods`, `abnormal_groups`, and `issue_groups` consistently. The zero-abnormal branch must clear all abnormal collections.

- [ ] **Step 6: Run focused tests**

Run the command from Step 2. Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add app/core/workflow/schemas.py app/core/workflow/nodes/layer_classifier.py tests/unit/workflow/test_context_handoff.py
git commit -m "fix: make current pod scan authoritative"
```

### Task 3: Render a deterministic HEALTHY report

**Files:**
- Modify: `tests/unit/workflow/test_conclusion_formatter.py`
- Modify: `app/core/workflow/nodes/conclusion_formatter.py`

- [ ] **Step 1: Write a failing report test**

Build a HEALTHY state whose `layer_handoff.current_abnormal_summary` contains `row_count=61`, `recent_restart_count=0`, and `restart_window_seconds=1800`, while old tool text contains cumulative restarts. Assert the report contains:

```python
assert "61" in report
assert "最近 30 分钟" in report
assert "未发现新增重启" in report
assert "历史累计重启次数不代表当前异常" in report
assert "HighRestarts" not in report
```

- [ ] **Step 2: Run the test and verify failure**

```bash
pytest -q tests/unit/workflow/test_conclusion_formatter.py -k healthy
```

Expected: current template lacks authoritative scan fields and may echo noisy tool text.

- [ ] **Step 3: Render only structured HEALTHY facts**

Parse `layer_analysis` as handoff JSON and render `row_count` and `restart_window_seconds // 60`. Do not append arbitrary Layer analysis or tool-result snippets in the HEALTHY path. The core lines are:

```python
f"- **检查范围**: 本轮扫描 {row_count} 个 Pod",
"- **运行状态**: 所有活跃 Pod 均为 Running，且 READY 完整",
f"- **重启窗口**: 最近 {window_minutes} 分钟未发现新增重启",
"- **说明**: 历史累计重启次数不代表当前异常",
```

- [ ] **Step 4: Run focused tests**

Run the command from Step 2. Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/core/workflow/nodes/conclusion_formatter.py tests/unit/workflow/test_conclusion_formatter.py
git commit -m "fix: render pod healthy facts deterministically"
```

### Task 4: Apply the abnormal-type Event plan policy

**Files:**
- Modify: `tests/unit/workflow/test_evidence_dynamic_stop.py`
- Modify: `app/core/workflow/nodes/evidence_collector.py`

- [ ] **Step 1: Write failing Event policy tests**

Test `_prepare_evidence_plan` with duplicate `kubectl_events` items for one Pod and handoffs for:

- `PendingUnschedulable`, `ImagePullFailed`, `VolumeMountFailed`, `SandboxCreateFailed`, `NotReadyProbeFailed`, `Evicted`, and `TerminatingStuck`: keep exactly one Event item per Pod.
- `CrashLoopBackOffRuntime` and `OOMKilled`: remove fixed Event items while preserving logs, metrics and YAML/describe items.
- `ConfigError`: keep Event only when status keywords/purpose mention a Kubernetes lifecycle Event reason such as `FailedMount` or `FailedCreate`.

- [ ] **Step 2: Run the policy tests and verify failure**

```bash
pytest -q tests/unit/workflow/test_evidence_dynamic_stop.py -k event_policy
```

Expected: current plan normalization keeps different Event purposes/commands for the same Pod.

- [ ] **Step 3: Implement plan filtering**

Add constants and helpers:

```python
_EVENT_REQUIRED_ABNORMAL_TYPES = {
    "pendingunschedulable", "imagepullfailed", "volumemountfailed",
    "sandboxcreatefailed", "notreadyprobefailed", "evicted",
    "terminatingstuck",
}

@classmethod
def _apply_event_policy(cls, plan, handoff):
    # Map Pod targets to issue-group abnormal types.
    # Drop Event items for types outside the matrix.
    # Deduplicate retained Event items by (namespace, pod), not purpose.
```

Call `_apply_event_policy` from `_prepare_evidence_plan` after normal plan normalization and again after legacy mandatory-plan normalization.

- [ ] **Step 4: Run focused tests**

Run the command from Step 2. Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/core/workflow/nodes/evidence_collector.py tests/unit/workflow/test_evidence_dynamic_stop.py
git commit -m "fix: route pod events by abnormal type"
```

### Task 5: Enforce one Event attempt per Pod at execution time

**Files:**
- Modify: `tests/unit/aicall/test_event_loop_safety.py`
- Modify: `app/core/aicall/client.py`
- Modify: `app/core/workflow/nodes/base.py`
- Modify: `app/core/workflow/nodes/evidence_collector.py`

- [ ] **Step 1: Write failing middleware tests**

Test that these calls share one execution signature:

```python
{"name": "kubectl_events", "args": {"namespace": "aaa", "resource_type": "pod", "resource_name": "p1", "purpose": "scheduling"}}
{"name": "kubectl_events", "args": {"namespace": "aaa", "resource_type": "pod", "resource_name": "p1", "purpose": "mount"}}
```

Different Pods must retain different signatures. Add async middleware tests proving that the second call returns `aiops_deduplicated=True` after the first success, empty result, or raised exception.

- [ ] **Step 2: Run tests and verify failure**

```bash
pytest -q tests/unit/aicall/test_event_loop_safety.py -k 'event_execution_signature or event_attempt'
```

Expected: purpose changes currently create different signatures, and failures are not cached.

- [ ] **Step 3: Canonicalize Event execution keys**

Special-case `kubectl_events` in `_tool_execution_signature`:

```python
if name.casefold() == "kubectl_events":
    namespace = str(args.get("namespace") or "").strip().casefold()
    pod = str(args.get("resource_name") or args.get("pod") or args.get("name") or "").strip().casefold()
    resource_type = str(args.get("resource_type") or "pod").strip().casefold()
    if namespace and pod and resource_type in {"pod", "pods"}:
        return f"name:kubectl_events|pod:{namespace}/{pod}"
```

- [ ] **Step 4: Support a cache shared across evidence rounds**

Add an optional mutable cache argument to `_build_tool_dedup_middleware`, `AICall.call`, and `WorkflowNode._call_llm`. Use the supplied cache instead of a new dict. Evidence execution creates one cache per `_execute_existing_evidence_plan` call and passes it into every collection round.

Cache a `kubectl_events` ToolMessage after the first attempt regardless of success/error status; retain success-only caching for other tools. The cloned message must carry `aiops_deduplicated=True` and the original call ID.

- [ ] **Step 5: Run focused tests**

Run the command from Step 2 plus:

```bash
pytest -q tests/unit/aicall/test_client.py tests/unit/workflow/test_evidence_dynamic_stop.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/core/aicall/client.py app/core/workflow/nodes/base.py app/core/workflow/nodes/evidence_collector.py tests/unit/aicall/test_event_loop_safety.py
git commit -m "fix: limit pod event collection to one attempt"
```

### Task 6: Align prompts, configuration, and documentation

**Files:**
- Modify: `app/core/prompts.py`
- Modify: `deploy/configmap/config.yaml`
- Modify: `README.md`
- Modify: `tests/unit/workflow/test_context_handoff.py` or a focused configuration test if one exists

- [ ] **Step 1: Add a failing configuration/default assertion**

Assert that the deployed configuration contains `restart_window_minutes: 30`, `event_policy.mode: by_abnormal_type`, and `max_calls_per_pod: 1`.

- [ ] **Step 2: Update prompt and configuration**

Replace fixed Event-first language with the matrix semantics. State explicitly that Kubernetes logs and Elastic logs are independent evidence sources and must both remain even if their content matches. Add:

```yaml
layer:
  health:
    restart_window_minutes: 30
    deterministic_fast_path: true
evidence:
  event_policy:
    mode: by_abnormal_type
    max_calls_per_pod: 1
```

- [ ] **Step 3: Update README**

Document the exact HEALTHY condition, positive recent-restart evidence, cumulative restart behavior, Event matrix, and fast-path call reduction.

- [ ] **Step 4: Run focused tests and diff checks**

```bash
pytest -q tests/unit/workflow/test_context_handoff.py -k config
git diff --check
```

Expected: PASS and no whitespace errors.

- [ ] **Step 5: Commit**

```bash
git add app/core/prompts.py deploy/configmap/config.yaml README.md tests/unit/workflow/test_context_handoff.py
git commit -m "docs: define pod health and event policy"
```

### Task 7: Regression and acceptance verification

**Files:**
- Test only; do not modify `deploy/secrets/core.yaml`.

- [ ] **Step 1: Run all unit tests**

```bash
pytest -q tests
```

Expected: all tests pass.

- [ ] **Step 2: Run anomaly Case tests**

```bash
pytest -q test/pod-anomaly-cases/tests
```

Expected: all tracked tests pass. If the known untracked-config ignore test still fails, report it separately and do not change or commit secrets/config credentials.

- [ ] **Step 3: Verify routing and sensitive-file isolation**

```bash
git status --short
git diff --check HEAD
git diff --name-only HEAD | rg 'deploy/secrets/core.yaml' && exit 1 || true
```

Expected: implementation changes do not include `deploy/secrets/core.yaml`.

- [ ] **Step 4: Review the final diff against acceptance requirements**

Confirm that:

- `RECENT_RESTART_WINDOW_SECONDS == 1800`;
- a confirmed zero-abnormal scan clears LLM HighRestarts and routes HEALTHY;
- Running/NotReady remains abnormal;
- HEALTHY does not execute Evidence/RCA/Event;
- Event plans follow the abnormal-type matrix;
- Event execution is capped at one attempt per Pod across evidence rounds;
- K8s and Elastic logs remain separate evidence dimensions.

- [ ] **Step 5: Commit any final test-only corrections**

```bash
git add tests/unit/aicall/test_observation_processing.py \
  tests/unit/aicall/test_event_loop_safety.py \
  tests/unit/workflow/test_context_handoff.py \
  tests/unit/workflow/test_conclusion_formatter.py \
  tests/unit/workflow/test_evidence_dynamic_stop.py
git commit -m "test: cover deterministic pod health routing"
```
