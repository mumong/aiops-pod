# Pod Abnormal Status Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/ask` diagnose Pod abnormal statuses first, while keeping `L0-L4` as derived compatibility layers.

**Architecture:** Keep the existing four-node workflow. Update prompt contracts, layer handoff fields, runtime runbook catalog, and tests so downstream nodes reason from `primary_pod`, `pod_status_keyword`, and `pod_abnormal_type`.

**Tech Stack:** Python, pytest, LangGraph workflow nodes, ConfigMap-backed runbooks.

---

### Task 1: Lock Prompt Contract With Tests

**Files:**
- Modify: `tests/unit/workflow/test_fast_paths.py`

- [ ] Add tests that assert the layer prompt defines all 11 Pod abnormal types, uses `derived_layer`, and treats `L0-L4` as compatibility fields.
- [ ] Run `./.venv/bin/pytest tests/unit/workflow/test_fast_paths.py -q` and verify the new tests fail before implementation.

### Task 2: Lock Handoff Contract With Tests

**Files:**
- Modify: `tests/unit/workflow/test_context_handoff.py`

- [ ] Add tests that assert `layer_handoff` contains `derived_layer` and `status_category`.
- [ ] Run `./.venv/bin/pytest tests/unit/workflow/test_context_handoff.py -q` and verify the new test fails before implementation.

### Task 3: Lock Runtime Catalog With Tests

**Files:**
- Modify: `tests/unit/runbook/test_runtime_catalog.py`
- Modify: `tests/unit/aicall/test_builtin_tools.py`

- [ ] Update catalog tests to expect Pod abnormal-status runbook IDs.
- [ ] Add a fetch allowlist test for one newly enabled Pod runbook.
- [ ] Run both tests and verify they fail before implementation.

### Task 4: Implement Prompt And Handoff Changes

**Files:**
- Modify: `app/core/prompts.py`
- Modify: `app/core/workflow/nodes/layer_classifier.py`

- [ ] Update `LAYER_CLASSIFIER_PROMPT` and `LAYER_EXTRACT_PROMPT` to define the 11 abnormal types.
- [ ] Add `derived_layer` and `status_category` to the required JSON contract.
- [ ] Add `derived_layer` and `status_category` to `layer_handoff`.
- [ ] Run workflow prompt and handoff tests.

### Task 5: Implement Runbook Catalog Changes

**Files:**
- Modify: `deploy/configmap/runbooks.yaml`
- Modify: `app/core/aicall/builtin_tools.py`

- [ ] Expand runtime catalog to Pod abnormal-status runbooks.
- [ ] Add compact runbook markdown entries for newly exposed status runbooks.
- [ ] Update `DEFAULT_ENABLED_RUNBOOK_IDS`.
- [ ] Run runbook and builtin tool tests.

### Task 6: Verify Focused Suite

**Files:**
- No production edits.

- [ ] Run `./.venv/bin/pytest tests/unit/workflow/test_fast_paths.py tests/unit/workflow/test_context_handoff.py tests/unit/runbook/test_runtime_catalog.py tests/unit/aicall/test_builtin_tools.py -q`.
- [ ] Fix any failures directly related to this change.
