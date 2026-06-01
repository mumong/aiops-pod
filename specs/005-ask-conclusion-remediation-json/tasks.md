# Tasks: Ask Conclusion Remediation JSON

**Input**: Design documents from `/specs/005-ask-conclusion-remediation-json/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/remediation-json-contract.md

**Tests**: Required by constitution and user request.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Phase 1: Setup

- [X] T001 Commit and push previous `/query` work to origin/qwen-before-architecture

---

## Phase 2: Foundational

- [X] T002 Add failing conclusion-node unit test in tests/unit/workflow/test_ask_conclusion_remediation_json.py for confirmed finalizer evidence with empty structured actions
- [X] T003 Add failing conclusion-node unit test in tests/unit/workflow/test_ask_conclusion_remediation_json.py for force-delete or missing-evidence safety regression
- [X] T004 Add query regression assertion proving the new normalization is not invoked for query direct rendering

---

## Phase 3: User Story 1 - Stable Safety Review Entry (Priority: P1) MVP

**Goal**: Confirmed finalizer repair has valid structured JSON actions.

**Independent Test**: Run the new conclusion-node test and parse the returned report with `extract_remediation_plan`.

- [X] T005 [US1] Add local ask-only remediation JSON normalization in app/core/workflow/nodes/conclusion_formatter.py
- [X] T006 [US1] Validate normalized plans through existing extract_remediation_plan before returning report

---

## Phase 4: User Story 2 - Preserve Unsafe and Ambiguous Cases (Priority: P1)

**Goal**: Do not synthesize unsafe actions.

**Independent Test**: Run safety regression test with force-delete advice and missing finalizer evidence.

- [X] T007 [US2] Gate synthesis on concrete pod/namespace/deletionTimestamp/finalizers evidence
- [X] T008 [US2] Preserve existing invalid/unavailable plan behavior when evidence is insufficient

---

## Phase 5: User Story 3 - Query and Earlier Nodes Unchanged (Priority: P1)

**Goal**: `/query`, layer, evidence, RCA remain unchanged.

**Independent Test**: Run existing query direct and remediation handling tests.

- [X] T009 [US3] Ensure normalization is called only for non-query conclusion output
- [X] T010 [US3] Run focused `/query` direct regression tests

---

## Phase 6: Validation

- [X] T011 Run focused pytest suite
- [X] T012 Run near-real workflow/executor validation showing parseable plan or approval event

## Dependencies & Execution Order

- T001 before all new implementation.
- T002-T004 before T005-T009.
- T005-T009 before validation.
- T011 before T012.

## Implementation Strategy

1. Prove the missing-action failure at conclusion level.
2. Add the smallest ask-only normalization helper.
3. Reuse existing remediation parser as the validation gate.
4. Verify query tests remain unaffected.
