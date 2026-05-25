# Remediation Approval Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional post-conclusion remediation executor that consumes structured remediation JSON and requires human approval before accepting the plan and before each write action.

**Architecture:** Keep the existing diagnosis workflow unchanged through conclusion. Conclusion will carry or expose a structured `remediation_plan`; executor code parses the plan and runs deterministic safe actions with approval gates. SSE/API approval state is implemented outside LLM calls to avoid extra node/LLM latency.

**Tech Stack:** Python, FastAPI, LangGraph workflow state, existing SSE event streaming, pytest.

---

### Task 1: Remediation Models and Parser

**Files:**
- Create: `app/core/remediation/models.py`
- Create: `app/core/remediation/plans.py`
- Test: `tests/unit/remediation/test_plans.py`

- [x] Write failing tests for extracting a JSON remediation plan from conclusion markdown and normalizing allowed actions.
- [x] Implement Pydantic/dataclass-like model helpers with no Kubernetes execution.
- [x] Run targeted pytest.

### Task 2: Approval Store

**Files:**
- Create: `app/core/remediation/approval.py`
- Test: `tests/unit/remediation/test_approval.py`

- [x] Write failing tests for creating approval requests, approving/rejecting, and timeout-safe polling.
- [x] Implement in-memory approval store keyed by run_id and approval_id.
- [x] Run targeted pytest.

### Task 3: Safe Remediation Executor

**Files:**
- Create: `app/core/remediation/executor.py`
- Test: `tests/unit/remediation/test_executor.py`

- [x] Write failing tests for plan approval gate, per-action approval gate, dry-run before execute, and stop on reject.
- [x] Implement executor as a generator yielding remediation events.
- [x] Use subprocess runner injection for tests; production runner calls kubectl commands only from allowed action types.

### Task 4: Workflow/API Integration

**Files:**
- Modify: `app/core/workflow/state.py`
- Modify: `app/core/workflow/executor.py`
- Modify: `app/api/routes.py`
- Test: existing compile/import tests plus targeted remediation tests.

- [x] Add remediation state fields and optional workflow config flags.
- [x] Append remediation execution after final report when enabled.
- [x] Add `/remediation/approve` API for approve/reject decisions.
- [x] Verify py_compile and tests.
