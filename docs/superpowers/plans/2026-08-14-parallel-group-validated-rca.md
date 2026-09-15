# Parallel Group Validated RCA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing multi-anomaly path reuse formal Fact Ledger-validated RCA per group and deterministically surface its decisive facts without changing the single path.

**Architecture:** Preserve parallel collector isolation, run the existing `RootCauseAnalyzerNode` inside each group worker, project its validated result into per-entity summaries, retain canonical FactRecord fields during group aggregation, and replace insertion-order presentation with RCA-reference ordering.

**Tech Stack:** Python 3, Pydantic, LangGraph workflow state, pytest.

---

### Task 1: Lossless multi-group fact projection

**Files:**
- Modify: `app/core/workflow/group_evidence.py`
- Test: `tests/unit/workflow/test_group_evidence.py`

- [ ] Add a failing test proving a Kubernetes canonical resource-limit record is used instead of the lossy Kubernetes summary fallback.
- [ ] Add a failing test proving metric `metadata.labels`, timestamps, and an unknown extension field survive projection and produce a distinguishing `display_value`.
- [ ] Run `pytest -q tests/unit/workflow/test_group_evidence.py` and confirm failures are caused by dropped canonical fields.
- [ ] Copy canonical records losslessly, add `display_value`, and generalize Fact Ledger aggregation to Kubernetes while retaining the legacy fallback.
- [ ] Re-run the focused test file and confirm it passes.

### Task 2: Formal validated RCA per parallel group

**Files:**
- Modify: `app/core/workflow/nodes/parallel_evidence.py`
- Test: `tests/unit/workflow/test_parallel_evidence.py`

- [ ] Add a failing integration-style unit test whose collector returns two entity-scoped Fact Ledgers and whose formal RCA output contains separate hypotheses.
- [ ] Assert the RCA receives the original `evidence_analysis`, the old `GroupDiagnosisSummaryOutput` call is absent, valid fact IDs remain entity-scoped, and unsupported entity claims are inconclusive.
- [ ] Run the exact new tests and confirm they fail because the parallel node still invokes the mini-RCA.
- [ ] Build a group-scoped `RootCauseAnalyzerNode`, run it after collection, retain `rca_analysis`, and map validated hypotheses to entity summaries.
- [ ] Re-run `tests/unit/workflow/test_parallel_evidence.py` and confirm it passes.

### Task 3: RCA-first deterministic report fan-in

**Files:**
- Modify: `app/core/workflow/nodes/conclusion_formatter.py`
- Test: `tests/unit/workflow/test_parallel_evidence.py`
- Test: `tests/unit/workflow/test_conclusion_formatter.py`

- [ ] Add a failing test with lifecycle facts inserted before a decisive RCA supporting fact and assert the supporting fact is displayed first with metric labels.
- [ ] Add a failing test proving multi-group conclusion does not invoke a narrative LLM that can override validated root causes.
- [ ] Run the exact tests and confirm failures match insertion-order rendering and the current narrative call.
- [ ] Implement deterministic group overview and evidence selection by validated supporting/contradicting fact references, then generic fact rendering from `display_value`.
- [ ] Re-run both focused test files and confirm they pass.

### Task 4: Regression and impact audit

**Files:**
- No additional production files.

- [ ] Run `pytest -q tests/unit/workflow/test_group_evidence.py tests/unit/workflow/test_parallel_evidence.py tests/unit/workflow/test_conclusion_formatter.py tests/unit/workflow/test_fact_contract.py tests/unit/workflow/test_context_handoff.py tests/unit/workflow/test_graph.py`.
- [ ] Run the repository's available lint or compile check for the modified Python modules.
- [ ] Inspect `git diff -- app/core/workflow/group_evidence.py app/core/workflow/nodes/parallel_evidence.py app/core/workflow/nodes/conclusion_formatter.py tests/unit/workflow` and verify no Case-specific or single-path branch was added.
- [ ] Run an offline multi-group fixture through `parallel_evidence -> conclusion` and inspect that each entity shows its validated root cause plus referenced Kubernetes/Metrics/Logging/Tracing facts.

