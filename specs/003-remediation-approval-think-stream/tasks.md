# Tasks: Remediation Approval And Think Stream

**Input**: Design documents from `specs/003-remediation-approval-think-stream/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Required. This feature changes remediation safety behavior and user-visible streaming behavior, and must use failing automated tests plus real validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare focused validation and remove ambiguity from stale controls.

- [X] T001 Inspect current remediation and think-stream tests in `tests/unit/api/test_query_routes.py`, `tests/unit/workflow/test_remediation_plan_handling.py`, `tests/unit/remediation/test_agent.py`, `tests/unit/remediation/test_executor.py`, `tests/unit/test_service_think_stream.py`, and `tests/unit/aicall/test_event_loop_safety.py`
- [X] T002 [P] Add shared remediation test fixtures or helpers in `tests/unit/workflow/test_remediation_plan_handling.py`
- [X] T003 [P] Add shared think stream test fixtures or helpers in `tests/unit/test_service_think_stream.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish control semantics that all user stories depend on.

**CRITICAL**: No user story implementation should start until these tests fail for the current behavior.

- [X] T004 Add failing tests proving `/ask` no longer requires `remediate=true` when workflow remediation is enabled in `tests/unit/api/test_query_routes.py`
- [X] T005 Add failing tests proving `AUTO_REMEDIATE` is not read for remediation prompt policy or execution mode in `tests/unit/workflow/test_remediation_plan_handling.py`
- [X] T006 Add failing tests proving review mode prompt policy allows planning write actions while requiring approval in `tests/unit/workflow/test_remediation_plan_handling.py`
- [X] T007 Remove request-level remediation override behavior from `app/api/routes.py`
- [X] T008 Remove `AUTO_REMEDIATE` remediation prompt policy from `app/core/workflow/nodes/base.py`
- [X] T009 Remove `AUTO_REMEDIATE` execution-control semantics from `app/core/aicall/builtin_tools.py`
- [X] T010 Update deployment config to remove `AUTO_REMEDIATE` env/secret wiring in `deploy/k8s-simple.yaml` and `deploy/secrets/core.yaml`
- [X] T011 Run foundational tests and confirm T004-T006 now pass with no regression in `tests/unit/api/test_query_routes.py` and `tests/unit/workflow/test_remediation_plan_handling.py`

---

## Phase 3: User Story 1 - Approval-Gated Remediation Plan Is Generated (Priority: P1) MVP

**Goal**: Confirmed repairable cases produce stable structured actions and review mode reaches approval instead of silently skipping.

**Independent Test**: Simulate a confirmed TerminatingStuck finalizer report and verify `remediation_available=true`, scoped patch action, plan/action approval in review mode, and `invalid_plan` for inconsistent repairable reports.

### Tests for User Story 1

- [X] T012 [P] [US1] Add failing parser/validation test for TerminatingStuck finalizer structured action in `tests/unit/remediation/test_plans.py`
- [X] T013 [P] [US1] Add failing workflow test for repairable natural-language advice with empty actions emitting `invalid_plan` in `tests/unit/workflow/test_remediation_plan_handling.py`
- [X] T014 [P] [US1] Add failing review-mode approval test with structured finalizer patch action in `tests/unit/remediation/test_agent.py`
- [X] T015 [P] [US1] Add failing conclusion/plan consistency test for finalizer repair output in `tests/unit/workflow/test_fast_paths.py`

### Implementation for User Story 1

- [X] T016 [US1] Strengthen remediation JSON extraction and validation behavior in `app/core/remediation/plans.py`
- [X] T017 [US1] Surface `invalid_plan` for enabled repairable cases with missing or inconsistent actions in `app/core/workflow/executor.py`
- [X] T018 [US1] Stabilize structured remediation action generation instructions for confirmed repairable cases in `app/core/workflow/nodes/conclusion_formatter.py`
- [X] T019 [US1] Ensure review mode emits plan approval and action approval before finalizer patch execution in `app/core/remediation/agent.py`
- [X] T020 [US1] Run US1 tests in `tests/unit/remediation/test_plans.py`, `tests/unit/remediation/test_agent.py`, `tests/unit/workflow/test_remediation_plan_handling.py`, and `tests/unit/workflow/test_fast_paths.py`

**Checkpoint**: User Story 1 is complete when ordinary `/ask` with remediation enabled in review mode can reach approval for a confirmed finalizer patch and cannot silently skip malformed repairable plans.

---

## Phase 4: User Story 2 - Auto Mode Means No Human Approval (Priority: P2)

**Goal**: Auto mode automatically approves safe actions while preserving command safety validation and verification.

**Independent Test**: Simulate the same structured plan in auto mode and verify safe action execution proceeds without approval events, while unsafe commands are rejected.

### Tests for User Story 2

- [X] T021 [P] [US2] Add failing auto-mode no-approval execution test in `tests/unit/remediation/test_agent.py`
- [X] T022 [P] [US2] Add failing deterministic executor auto-mode behavior test in `tests/unit/remediation/test_executor.py`
- [X] T023 [P] [US2] Add failing unsafe-command rejection test for auto mode in `tests/unit/remediation/test_plans.py`

### Implementation for User Story 2

- [X] T024 [US2] Normalize `workflow.remediation.mode` handling and defaults in `app/core/workflow/executor.py`
- [X] T025 [US2] Verify auto mode bypasses approval waits but not safe-command validation in `app/core/remediation/agent.py`
- [X] T026 [US2] Verify deterministic executor matches review/auto semantics in `app/core/remediation/executor.py`
- [X] T027 [US2] Run US2 tests in `tests/unit/remediation/test_agent.py`, `tests/unit/remediation/test_executor.py`, and `tests/unit/remediation/test_plans.py`

**Checkpoint**: User Story 2 is complete when auto mode executes safe validated actions without approval prompts and rejects unsupported commands.

---

## Phase 5: User Story 3 - Think Stream Is Visible And Diagnosable (Priority: P3)

**Goal**: Streaming output shows available LLM intermediate reasoning and always preserves auditable progress fallback events.

**Independent Test**: Simulate `<think>`, provider `reasoning_content`, ordinary AI message reasoning, hidden/truncated/full modes, and non-token-streaming node paths.

### Tests for User Story 3

- [X] T028 [P] [US3] Add failing tests for provider reasoning and ordinary AI message reasoning rendering in `tests/unit/test_service_think_stream.py`
- [X] T029 [P] [US3] Add failing tests for token-stream reasoning extraction in `tests/unit/aicall/test_event_loop_safety.py`
- [X] T030 [P] [US3] Add failing workflow text-rendering tests for progress fallback and no dropped complete messages in `tests/unit/workflow/test_remediation_plan_handling.py`

### Implementation for User Story 3

- [X] T031 [US3] Update reasoning extraction and event payloads in `app/core/aicall/client.py`
- [X] T032 [US3] Update think filtering for full/truncated/hidden modes in `app/core/service.py`
- [X] T033 [US3] Preserve complete AI message visibility after token streaming and keep tool/progress events visible in `app/core/service.py`
- [X] T034 [US3] Include remediation approval/progress events in user-visible stream rendering in `app/core/service.py`
- [X] T035 [US3] Run US3 tests in `tests/unit/test_service_think_stream.py`, `tests/unit/aicall/test_event_loop_safety.py`, and `tests/unit/workflow/test_remediation_plan_handling.py`

**Checkpoint**: User Story 3 is complete when full mode shows available LLM reasoning, hidden mode hides raw reasoning, truncated mode truncates safely, and all modes preserve auditable progress.

---

## Phase 6: Documentation, Deployment, And Real Validation

**Purpose**: Update operator docs and prove behavior in the real deployed service.

- [X] T036 [P] Update remediation usage docs to remove `remediate=true` and `AUTO_REMEDIATE` control semantics in `docs/remediation-usage.md`
- [X] T037 [P] Update general guide references for remediation mode control in `docs/GUIDE.md`
- [X] T038 [P] Update config comments for canonical remediation mode in `deploy/configmap/config.yaml`
- [X] T039 Run focused automated verification from `specs/003-remediation-approval-think-stream/quickstart.md`
- [X] T040 Set deployment version according to `specs/003-remediation-approval-think-stream/spec.md` in `VERSION`
- [X] T041 Run deployment commands from `specs/003-remediation-approval-think-stream/quickstart.md`
- [X] T042 Validate rollout and health using commands in `specs/003-remediation-approval-think-stream/quickstart.md`
- [X] T043 Run real review-mode `/ask` from `specs/003-remediation-approval-think-stream/quickstart.md` without `remediate=true` and verify `remediation_approval_required` with finalizer patch action
- [X] T044 Run real think stream `/query` from `specs/003-remediation-approval-think-stream/quickstart.md` and verify visible LLM reasoning when available or visible tool/progress fallback
- [X] T045 Record real validation outputs and any report/archive paths in `specs/003-remediation-approval-think-stream/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories.
- **US1 (Phase 3)**: Depends on Foundational; MVP scope.
- **US2 (Phase 4)**: Depends on Foundational and should reuse US1 structured action fixtures.
- **US3 (Phase 5)**: Depends on Foundational; can proceed in parallel with US1/US2 after shared stream fixtures exist.
- **Validation (Phase 6)**: Depends on selected user stories and automated tests passing.

### User Story Dependencies

- **US1**: Required MVP. Establishes stable structured actions and invalid-plan behavior.
- **US2**: Builds on the same remediation mode contract and safe-command validation as US1.
- **US3**: Independent of remediation execution logic after foundational request/config semantics are complete.

### Parallel Opportunities

- T002 and T003 can run in parallel.
- T012-T015 can run in parallel because they touch different test modules.
- T021-T023 can run in parallel because they touch different test modules.
- T028-T030 can run in parallel because they touch different test modules.
- T036-T038 can run in parallel after implementation is complete.

---

## Parallel Example: User Story 1

```text
Task: "T012 Add failing parser/validation test for TerminatingStuck finalizer structured action in tests/unit/remediation/test_plans.py"
Task: "T013 Add failing workflow test for repairable natural-language advice with empty actions emitting invalid_plan in tests/unit/workflow/test_remediation_plan_handling.py"
Task: "T014 Add failing review-mode approval test with structured finalizer patch action in tests/unit/remediation/test_agent.py"
Task: "T015 Add failing conclusion/plan consistency test for finalizer repair output in tests/unit/workflow/test_fast_paths.py"
```

## Parallel Example: User Story 3

```text
Task: "T028 Add failing tests for provider reasoning and ordinary AI message reasoning rendering in tests/unit/test_service_think_stream.py"
Task: "T029 Add failing tests for token-stream reasoning extraction in tests/unit/aicall/test_event_loop_safety.py"
Task: "T030 Add failing workflow text-rendering tests for progress fallback and no dropped complete messages in tests/unit/workflow/test_remediation_plan_handling.py"
```

---

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational phases.
2. Complete US1 only.
3. Validate review mode reaches approval for a stable structured finalizer patch action and surfaces `invalid_plan` for malformed repairable plans.
4. Stop and verify before adding auto-mode and think-stream changes.

### Incremental Delivery

1. US1: stable review-mode remediation planning and invalid-plan behavior.
2. US2: auto-mode semantics and safe execution.
3. US3: think stream reasoning/progress visibility.
4. Documentation and real deployment validation.

### Safety Notes

- Never infer write commands from prose during execution.
- Keep `workflow.remediation.mode` as the only execution-mode source.
- Preserve approval gates in review mode.
- Auto mode is for controlled validation and must still enforce safe-command policy.
