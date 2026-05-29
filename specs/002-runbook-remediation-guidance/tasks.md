# Tasks: Runbook Remediation Guidance

**Input**: Design documents from `specs/002-runbook-remediation-guidance/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Required. This feature changes model-facing behavior and must use TDD plus real validation.

## Phase 1: Setup

**Purpose**: Preserve the current active runbook and prepare validation.

- [x] T001 Create `docs/runbooks-backups/runbooks-2026-05-29-before-remediation-guidance.yaml` from current `deploy/configmap/runbooks.yaml`
- [x] T002 Update `.specify/feature.json` and `AGENTS.md` to point to `specs/002-runbook-remediation-guidance/plan.md`

---

## Phase 2: Tests First

**Purpose**: Prove the current runbooks do not yet satisfy the new remediation guidance contract.

- [x] T003 [P] Add failing runbook guidance validation tests in `test/workflow/test_runbook_remediation_guidance.py`
- [x] T004 Run `python3 -m unittest test.workflow.test_runbook_remediation_guidance` and confirm it fails on missing `## 标准修复建议`

---

## Phase 3: User Story 1 - Agent Gets Safe Case-Specific Repairs (Priority: P1)

**Goal**: TerminatingStuck guidance prefers confirmed finalizer patch and demotes force deletion.

**Independent Test**: Focused unit test validates TerminatingStuck ordering and branch exclusions.

- [x] T005 [US1] Update `pod-terminating-stuck.md` inside `deploy/configmap/runbooks.yaml` with finalizer, node/kubelet, volume, grace-period, and force-delete fallback guidance
- [x] T006 [US1] Run focused test and confirm TerminatingStuck assertions pass

---

## Phase 4: User Story 2 - Runbooks Stay Compact And Actionable (Priority: P2)

**Goal**: All active Pod abnormal-status runbooks have concise standard repair guidance.

**Independent Test**: Focused unit test validates targeted runbook section coverage.

- [x] T007 [US2] Add `## 标准修复建议` sections to the remaining active Pod runbooks in `deploy/configmap/runbooks.yaml`
- [x] T008 [US2] Run `python3 -m unittest test.workflow.test_runbook_remediation_guidance` and confirm all automated guidance checks pass

---

## Phase 5: Release And Real Validation (Priority: P3)

**Goal**: Deploy version `11.0.0` and verify the behavior through the live service.

**Independent Test**: Live `/ask` output and deployed Pod image show the new version and guidance.

- [x] T009 [US3] Set `VERSION` to `11.0.0`
- [x] T010 [US3] Run `make delete`, `make build`, `make push`, and `make deploy`
- [x] T011 [US3] Run health check and real `/ask` TerminatingStuck query; copied generated report to `/tmp/aiops-runbook-remediation-11.0.0-report.md`
- [x] T012 [US3] Inspect deployed output for finalizer patch guidance and no first-line force delete recommendation

## Validation Notes

- `curl --max-time 900 ... stream=false` timed out with 0 HTTP bytes, but server logs show the workflow completed and saved `/tmp/aiops/reports/L1-请诊断 aiops-e2e 命名空间 terminating_20260529_062955.md`.
- The saved report was copied locally to `/tmp/aiops-runbook-remediation-11.0.0-report.md` and contains the expected `kubectl patch pod ... finalizers:null` remediation. It does not contain `delete --force`.
- Deployment was restarted after the timed-out HTTP request to restore health; final health checks passed through NodePort.

---

## Dependencies & Execution Order

- Phase 1 must precede edits.
- Phase 2 must fail before runbook implementation.
- US1 should be completed before broad runbook updates because it is the risk-driving case.
- US2 can follow US1 in the same file.
- US3 depends on automated validation passing.

## Parallel Opportunities

- T003 can be prepared while T001/T002 are checked, but active file edits must wait for the failing test result.
- No runbook file edits should run in parallel because all active runbooks live in one YAML file.

## Implementation Strategy

Deliver the TerminatingStuck finalizer guidance first, then apply the same compact section pattern to the remaining runbooks, then deploy and verify through the real service.
