# Remediation Agent Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add configurable deterministic vs LLM-guided remediation execution, stricter post-fix verification, and reorganized `config.yaml` sections.

**Architecture:** Keep conclusion-generated `remediation_plan` as the entry contract. Add an LLM-guided ReAct loop that alternates decision -> approval -> command execution -> observation until fixed, failed, or bounded by configured limits. Preserve the existing deterministic executor as the default-compatible path.

**Tech Stack:** Python dataclasses, existing `AICall.call_structured`/JSON fallback, existing approval store, pytest, Kubernetes `kubectl` command runner.

---

### Task 1: Add tests for configurable executor selection and strict remediation verification

**Files:**
- Modify: `tests/unit/remediation/test_executor.py`
- Create: `tests/unit/remediation/test_agent.py`

- [ ] Add a test that deterministic execution can report `needs_followup` when verify output shows `CrashLoopBackOff` or `OOMKilled`.
- [ ] Add a test that agent mode accepts a fake LLM decision, executes one approved write action, observes an unhealthy pod, then stops as failed after max iterations.
- [ ] Add a test that agent mode succeeds only when observation contains Ready/Running and no recent OOM signal.

### Task 2: Implement remediation result analysis and agent loop

**Files:**
- Create: `app/core/remediation/agent.py`
- Modify: `app/core/remediation/models.py`
- Modify: `app/core/remediation/executor.py`

- [ ] Add small dataclasses for agent config and decisions.
- [ ] Add deterministic health classifier for command observations.
- [ ] Add `RemediationAgentExecutor.run()` that yields approval/tool/final events.
- [ ] Preserve current approval behavior for write actions.

### Task 3: Wire config selection into workflow executor

**Files:**
- Modify: `app/core/workflow/executor.py`
- Modify: `app/core/service.py` if needed for request-scoped `ai_call`

- [ ] Read `workflow.remediation.executor`: `deterministic` or `react`.
- [ ] Read `max_iterations`, `max_write_actions`, `verify_settle_seconds`, `max_duration_seconds`.
- [ ] Pass conclusion report and `ai_call` to the agent executor.
- [ ] Keep deterministic path as fallback.

### Task 4: Reorganize ConfigMap comments and remediation config

**Files:**
- Modify: `deploy/configmap/config.yaml`

- [ ] Add top-level comment index.
- [ ] Group sections as LLM, language, tools, workflow, remediation, stream/context, metrics, federation.
- [ ] Add remediation executor options and safety limits.
- [ ] Keep existing values functionally compatible.

### Task 5: Verify

**Commands:**
- `pytest tests/unit/remediation -q`
- `pytest tests/unit/api/test_query_routes.py -q`
- `python -m py_compile app/core/remediation/*.py app/core/workflow/executor.py app/core/service.py app/api/routes.py`
