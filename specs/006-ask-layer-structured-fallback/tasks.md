# Tasks: Ask Layer Structured Fallback

**Input**: Design documents from `/specs/006-ask-layer-structured-fallback/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Required because this is a bug fix and the user requested real validation.

## Phase 1: Setup

- [x] T001 Update Speckit feature pointer in `.specify/feature.json`
- [x] T002 Update AGENTS.md Speckit plan pointer to `specs/006-ask-layer-structured-fallback/plan.md`

## Phase 2: User Story 1 - Clear LLM Unavailable Failure (Priority: P1)

**Independent Test**: Simulate synthetic LLM connection failure and verify clear error without duplicate extraction.

- [x] T003 [P] [US1] Add failing unit test in `tests/unit/workflow/test_fast_paths.py`
- [x] T004 [US1] Implement LLM-unavailable detection in `app/core/workflow/nodes/layer_classifier.py`

## Phase 3: User Story 2 - Structured Fallback When Native Pydantic Is Unsupported (Priority: P1)

**Independent Test**: Verify layer extraction passes `allow_text_fallback=True` and accepts validated fallback JSON.

- [x] T005 [P] [US2] Add failing unit test in `tests/unit/workflow/test_fast_paths.py`
- [x] T006 [US2] Pass text fallback option from layer extraction in `app/core/workflow/nodes/layer_classifier.py`

## Phase 4: User Story 3 - Query Path Unchanged (Priority: P1)

**Independent Test**: Existing query direct tests continue to pass.

- [x] T007 [US3] Run focused query direct tests in `tests/unit/workflow/test_query_direct_mode.py`

## Phase 5: Real Validation

- [x] T008 Build and deploy image from version `11.0.5`
- [x] T009 Run real `/ask` validation and inspect backend logs
- [ ] T010 If LLM endpoint remains unreachable, report operational blocker with exact endpoint and log evidence

## Dependencies & Execution Order

T001-T002 first, then T003 before T004 and T005 before T006. T007-T010 after implementation.
