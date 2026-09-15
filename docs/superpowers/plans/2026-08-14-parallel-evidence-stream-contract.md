# Parallel Evidence Stream Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reliably attribute concurrent parallel-evidence tool events using structured group/entity context instead of truncated previews.

**Architecture:** Wrap each scoped parallel collector's event queue with its authoritative handoff group identity. Project a compact Pydantic-validated context through SSE and consume it in the Frontend with call-ID pairing and preview fallback compatibility.

**Tech Stack:** Python, Pydantic, LangGraph event queues, React, TypeScript, Node test runner, pytest.

---

### Task 1: Backend stream contract

**Files:**
- Create: `app/core/workflow/stream_contract.py`
- Modify: `app/core/workflow/nodes/parallel_evidence.py`
- Modify: `app/core/workflow/executor.py`
- Test: `tests/unit/workflow/test_parallel_evidence_stream.py`

- [ ] Write failing tests for validated exact entity context, group-only context, parallel-only full summary projection, and unchanged non-parallel projection.
- [ ] Run the focused pytest file and confirm failures are caused by the missing contract.
- [ ] Implement the scoped queue wrapper, Pydantic contract builder, and minimal executor projection.
- [ ] Run the focused Backend tests until green.

### Task 2: Frontend structured grouping

**Files:**
- Modify: `../frountind/src/components/aiops-chat/types.ts`
- Modify: `../frountind/src/components/aiops-chat/parallelEvidenceModel.ts`
- Modify: `../frountind/src/components/aiops-chat/ChatWidget.tsx`
- Modify: `../frountind/src/components/aiops-chat/ParallelEvidenceBoard.tsx`
- Test: `../frountind/tests/parallel-evidence-model.test.mjs`
- Test: `../frountind/tests/node-block-updates.test.mjs`

- [ ] Write failing tests for truncated previews with structured group context, exact same-name call-ID pairing, group-only results without entity fabrication, and semantic failure status.
- [ ] Run focused Node tests and confirm the expected failures.
- [ ] Implement structured context consumption, full processed summary details, and artifact-reference rendering while keeping preview parsing as fallback.
- [ ] Run focused Frontend tests until green.

### Task 3: Regression and acceptance

**Files:**
- No additional production files.

- [ ] Run relevant Backend workflow, context-handoff, and parallel-evidence tests.
- [ ] Run the complete Frontend test, lint, TypeScript, and production build checks.
- [ ] Verify the diff contains no MCP, diagnosis, final-report, remediation, deployment, Makefile, or secret changes from this task.
- [ ] Exercise a real multi-group SSE run only after deployment is separately authorized; otherwise provide the exact deployment/runtime acceptance commands without mutating the cluster.
