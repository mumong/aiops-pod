# Tasks: Query Direct Render

**Input**: Design documents from `/specs/004-query-direct-render/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/query-direct-contract.md

**Tests**: Required by constitution and user request.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Phase 1: Setup

- [X] T001 Review historical query direct implementation before security-review changes using git history

---

## Phase 2: Foundational

- [X] T002 Add failing query conclusion test in tests/unit/workflow/test_query_direct_mode.py proving valid `query_result` renders locally without LLM calls
- [X] T003 Add failing query layer test in tests/unit/workflow/test_query_direct_mode.py proving usable Prometheus tool results skip Pydantic `layer_extract` even without an early_stop event
- [X] T004 Add or adjust non-query regression test in tests/unit/workflow/test_fast_paths.py proving diagnosis conclusion still uses the existing diagnosis path

---

## Phase 3: User Story 1 - Fast Metric Query Result (Priority: P1) MVP

**Goal**: `/query` returns a deterministic Markdown table from `query_result`.

**Independent Test**: Run focused query direct tests and verify no conclusion LLM call occurs when `query_result` exists.

- [X] T005 [US1] Update query conclusion rendering in app/core/workflow/nodes/conclusion_formatter.py
- [X] T006 [US1] Update query direct layer extraction shortcut in app/core/workflow/nodes/layer_classifier.py

---

## Phase 4: User Story 2 - Preserve Ask Diagnosis Flow (Priority: P1)

**Goal**: `/ask` remains unchanged.

**Independent Test**: Run existing diagnosis/remediation focused tests.

- [X] T007 [US2] Ensure query-only branches are gated by `query_mode=direct` and `layer=QUERY`
- [X] T008 [US2] Run focused `/ask` regression tests

---

## Phase 5: User Story 3 - Avoid Query Planning Noise (Priority: P2)

**Goal**: Query output excludes TodoWrite and metadata-as-metric noise.

**Independent Test**: Run tests with TodoWrite and node metadata tool events.

- [X] T009 [US3] Filter metadata Prometheus queries from metric columns in app/core/workflow/nodes/layer_classifier.py
- [X] T010 [US3] Verify TodoWrite remains excluded from query data

---

## Phase 6: Validation

- [X] T011 Run focused pytest suite
- [X] T012 Run real `/query` validation on deployed Pod and inspect output/logs

## Dependencies & Execution Order

- T001 before implementation.
- T002-T004 before T005-T007.
- T005-T010 before validation.
- T011 before T012.

## Implementation Strategy

1. Restore the deterministic query render MVP first.
2. Remove the avoidable query direct layer_extract latency.
3. Preserve `/ask` through focused regression tests.
4. Validate with real `/query` output.
