# First-Principles Prompt Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Distill global Codex intent handling and contract the active K8s workflow prompts while preserving evidence, scope, coverage, and remediation behavior.

**Architecture:** Global guidance owns intent distillation across repositories. `app/core/prompts.py` remains the runtime source of truth, with active node prompts reduced to objective, authority, actions/stops, output, and high-cost boundaries. Tests enforce character ceilings and prohibit runtime injection of prompt-authoring methodology.

**Tech Stack:** Markdown `AGENTS.md`, Python string prompts, pytest, Pydantic workflow schemas.

---

## File map

- Modify `/root/.codex/AGENTS.md`: add compact global intent and prompt-authoring rules.
- Modify `app/core/prompts.py`: remove the dead long conclusion assignment and contract active layer, query, evidence, and RCA prompts.
- Modify `tests/unit/workflow/test_fast_paths.py`: add prompt budget and governance tests; retain behavior assertions.
- Create `docs/prompt-governance.md`: document the prompt source, editing rules, budgets, and checks.
- Modify `README.md`: link the prompt governance guide.

### Task 1: Add global intent distillation

**Files:**
- Modify: `/root/.codex/AGENTS.md`

- [ ] **Step 1: Verify the new section is absent**

Run:

```bash
rg -n '^# Intent and prompt distillation$' /root/.codex/AGENTS.md
```

Expected: exit code 1.

- [ ] **Step 2: Append the compact global contract**

Add exactly:

```markdown
# Intent and prompt distillation

- Before acting, internally reduce the request to objective, authoritative context, deliverable, hard constraints, and completion evidence. Preserve material ambiguity; do not invent intent.
- Prefer a high-signal example, schema, command, or acceptance check over repeated explanation. Keep each rule once, near the decision it governs.
- Keep negative rules only for probable, costly drift; pair each prohibition with the required alternative behavior.
- When creating prompts, encode the task contract instead of teaching the prompt-writing method. Do not expose private chain-of-thought or restate the full request unless clarification is necessary.
- Keep progress and final responses proportional to the task; lead with the outcome and include only details that help verification or the next decision.
```

- [ ] **Step 3: Verify global scope and uniqueness**

Run:

```bash
test "$(rg -c '^# Intent and prompt distillation$' /root/.codex/AGENTS.md)" = 1
sha256sum /root/.codex/AGENTS.md
```

Expected: exit code 0 and one checksum line. Do not commit this file because it is outside the repository.

### Task 2: Lock prompt governance with failing tests

**Files:**
- Modify: `tests/unit/workflow/test_fast_paths.py`

- [ ] **Step 1: Add the budget and methodology tests**

```python
def test_active_workflow_prompts_stay_within_attention_budgets():
    budgets = {
        "layer": 2600,
        "layer_extract": 1400,
        "layer_query_direct": 1900,
        "evidence": 4000,
        "rca": 4300,
        "conclusion": 1200,
    }
    for name, ceiling in budgets.items():
        assert len(get_workflow_prompt(name)) <= ceiling


def test_runtime_prompts_encode_tasks_not_prompt_methodology():
    active = "\n".join(
        get_workflow_prompt(name)
        for name in (
            "layer", "layer_extract", "layer_query_direct",
            "evidence", "rca", "conclusion",
        )
    )
    for phrase in ("第一性原理", "隐性提纯", "负向配平", "高维潜空间"):
        assert phrase not in active
```

- [ ] **Step 2: Run and verify RED**

```bash
pytest -q \
  tests/unit/workflow/test_fast_paths.py::test_active_workflow_prompts_stay_within_attention_budgets \
  tests/unit/workflow/test_fast_paths.py::test_runtime_prompts_encode_tasks_not_prompt_methodology
```

Expected: budget test fails for layer, layer extract, query direct, evidence, and RCA; methodology test passes.

- [ ] **Step 3: Commit the RED tests**

```bash
git add tests/unit/workflow/test_fast_paths.py
git commit -m "test: set active workflow prompt budgets"
```

### Task 3: Contract layer and query prompts

**Files:**
- Modify: `app/core/prompts.py:113-317`
- Test: `tests/unit/workflow/test_fast_paths.py`

- [ ] **Step 1: Replace the three active prompt bodies**

Use these blocks and retain the exact phrases already asserted by focused tests:

```text
Layer classifier
  Objective: scan current Pods, identify every current abnormal Pod/group,
             map the compatibility layer, then stop.
  Authority: current global Pod scan; events/runbooks are context only.
  Actions: global scan first; target-scoped requests stay scoped; fetch one
           matching runbook per distinct type; stop before deep evidence.
  Output: LayerOutput fields only.
  Boundaries: no final report, remediation, deep collection, historical Pod
              creation, or primary-Pod collapse.

Layer extract
  Objective: map existing analysis into LayerOutput without tools.
  Authority: current scan beats historical events.
  Output: retain all current abnormal Pods/groups and stable taxonomy fields.

Query direct
  Objective: answer only requested query items with real tool results.
  Actions: list requested items, use the PromQL runbook when applicable,
           collect each item, mark missing items, stop when complete.
  Output: pure JSON query_result for local rendering.
```

Keep the real ecosystem anchors `kubectl_get_by_kind_in_cluster(kind="Pod")`, `kubectl get pods -A`, `fetch_runbook`, and `private-k8s-query-promql-reference.md`; remove prose examples that repeat the same classification.

- [ ] **Step 2: Run the layer/query prompt tests**

```bash
pytest -q tests/unit/workflow/test_fast_paths.py -k 'layer_prompt or layer_extract_prompt or query_direct_prompt or active_workflow_prompts'
```

Expected: exit code 0.

- [ ] **Step 3: Commit**

```bash
git add app/core/prompts.py tests/unit/workflow/test_fast_paths.py
git commit -m "refactor: distill layer and query prompts"
```

### Task 4: Contract evidence collection

**Files:**
- Modify: `app/core/prompts.py:319-447`
- Test: `tests/unit/workflow/test_fast_paths.py`

- [ ] **Step 1: Replace repeated evidence rules with one decision loop**

The final prompt must encode:

```text
Objective -> cover every current abnormal group with source-backed evidence.
Plan -> execute the existing Pydantic plan; a plan/runbook/archive is not evidence.
First round -> Kubernetes identity/lifecycle plus execute_pod_promql,
               query_pod_logs, query_pod_tracing for every confirmed abnormal Pod.
Interpret -> preserve facts/samples/query/evidence_refs and coverage exactly.
Refine -> add a query only when the previous result leaves a named ambiguity;
          no fixed fault-name tool chain.
Stop -> critical/important purpose answered, duplicate call avoided, or context 80%.
Output -> short collected/missing/conflict summary for schema extraction.
```

Keep existing exact test phrases for mixed-source coverage, trace separation, YAML intent, runbook reuse, NotFound conflicts, and generic first-round tools. Remove the repeated copies in `EVIDENCE_PLAN_PROTOCOL_*`; those constants keep only execution-state differences.

- [ ] **Step 2: Run evidence prompt tests**

```bash
pytest -q \
  tests/unit/workflow/test_fast_paths.py -k 'evidence_prompt or aiops_prompts or prompts_refine or active_workflow_prompts' \
  tests/unit/workflow/test_evidence_dynamic_stop.py
```

Expected: exit code 0.

- [ ] **Step 3: Commit**

```bash
git add app/core/prompts.py tests/unit/workflow/test_fast_paths.py
git commit -m "refactor: distill evidence collection prompt"
```

### Task 5: Contract RCA and remove the dead conclusion prompt

**Files:**
- Modify: `app/core/prompts.py:480-796`
- Test: `tests/unit/workflow/test_fast_paths.py`
- Test: `tests/unit/workflow/test_fact_contract.py`

- [ ] **Step 1: Remove the overwritten long `CONCLUSION_FORMATTER_PROMPT` assignment**

Keep only the compact active assignment beginning with `# 任务`. The removed block is dead at runtime and duplicates evidence/report validators.

- [ ] **Step 2: Reduce RCA to the validated decision contract**

Retain:

```text
Objective -> produce RCAOutput from existing evidence; never call tools.
Authority -> Fact Ledger facts and valid IDs; current entity and current window.
Diagnosed gate -> valid same-entity supporting fact with required directness/confidence.
Inconclusive gate -> invalid/no/coverage-only/weak/related-context support.
Evidence fidelity -> exact decisive values, messages, trace IDs, duration semantics,
                     Tempo attributes, and topology direction/strength.
Output -> RCAOutput fields; JSON-only text fallback when native structured output
          is unavailable; no Markdown or code fence.
```

Remove the full hand-written JSON example. The Pydantic schema is the implicit output example; list required field names once and retain the current scalar/list/object constraints.

- [ ] **Step 3: Run RCA/conclusion contract tests**

```bash
pytest -q \
  tests/unit/workflow/test_fast_paths.py -k 'rca_prompt or rca_and_conclusion or fixture_free or active_workflow_prompts' \
  tests/unit/workflow/test_fact_contract.py
```

Expected: exit code 0.

- [ ] **Step 4: Commit**

```bash
git add app/core/prompts.py tests/unit/workflow/test_fast_paths.py
git commit -m "refactor: distill RCA prompt contracts"
```

### Task 6: Document and verify prompt governance

**Files:**
- Create: `docs/prompt-governance.md`
- Modify: `README.md`

- [ ] **Step 1: Document source and editing rules**

Document `app/core/prompts.py` as the runtime prompt source; explain the five-block contract, implicit carriers, negative-rule threshold, budgets, TDD commands, and why authoring-method vocabulary is not injected at runtime. State that `/root/.codex/AGENTS.md` is personal global guidance and is not part of the repository.

- [ ] **Step 2: Link the guide from README**

Add `docs/prompt-governance.md` under reference documents.

- [ ] **Step 3: Run final verification**

```bash
pytest -q \
  tests/unit/workflow/test_fast_paths.py \
  tests/unit/workflow/test_fact_contract.py \
  tests/unit/workflow/test_evidence_dynamic_stop.py \
  tests/unit/workflow/test_ask_conclusion_remediation_json.py \
  tests/unit/remediation/test_plans.py
git diff --check
rg -n 'if .*OOM|elif .*OOM|match .*OOM' \
  app/core/workflow/report_presentation.py app/core/prompts.py
```

Expected: tests exit 0; whitespace check exits 0; genericity scan finds no production conditional branch.

- [ ] **Step 4: Print the before/after prompt table and global checksum**

Use Python to print each active prompt length and verify it is within the tested ceiling. Run `sha256sum /root/.codex/AGENTS.md` and record the result.

- [ ] **Step 5: Commit documentation**

```bash
git add README.md docs/prompt-governance.md
git commit -m "docs: document prompt governance"
```
