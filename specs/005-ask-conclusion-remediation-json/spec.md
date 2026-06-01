# Feature Specification: Ask Conclusion Remediation JSON

**Feature Branch**: `005-ask-conclusion-remediation-json`

**Created**: 2026-06-01

**Status**: Draft

**Input**: User description: "Use Speckit to stabilize only the final `/ask` conclusion layer that decides whether a structured remediation plan should enter safety review. First commit and push previous work to origin/qwen-before-architecture. Then implement incrementally. Only change ask conclusion logic; do not change query, layer, evidence, or RCA."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stable Safety Review Entry (Priority: P1)

An operator runs `/ask` and the final diagnosis identifies a safe, evidence-backed Kubernetes repair. The report includes a valid structured remediation JSON plan so the workflow enters the existing safety review / approval path.

**Why this priority**: The reported failure is that natural-language repair advice can exist while structured actions are missing, so the executor cannot create approval.

**Independent Test**: Feed the conclusion node a diagnosis report for a confirmed TerminatingStuck finalizer case and verify the returned report contains a valid `remove_finalizer` action that `extract_remediation_plan` can parse.

**Acceptance Scenarios**:

1. **Given** `/ask` conclusion context contains current Pod evidence with `deletionTimestamp` and non-empty `metadata.finalizers`, **When** the final report suggests finalizer removal but JSON is missing or empty, **Then** conclusion normalizes the report to include a valid structured patch action.
2. **Given** the normalized report is consumed by the workflow executor, **When** remediation is enabled in review mode, **Then** the existing remediation approval event can be produced without adding a new gate or changing approval semantics.

---

### User Story 2 - Preserve Unsafe and Ambiguous Cases (Priority: P1)

An operator runs `/ask` where evidence is insufficient or the natural-language repair is unsafe. The system must not invent a structured write action.

**Why this priority**: Stabilizing approval entry must not lower the safety bar.

**Independent Test**: Feed the conclusion node reports with force-delete advice, missing finalizer evidence, or placeholder targets and verify no structured write action is synthesized.

**Acceptance Scenarios**:

1. **Given** the report suggests `kubectl delete --force`, **When** finalizer evidence is not confirmed, **Then** conclusion leaves the structured plan unavailable or invalid for executor rejection.
2. **Given** a report contains placeholders such as `<pod>` or `<namespace>`, **When** conclusion normalizes remediation JSON, **Then** no executable action is created.

---

### User Story 3 - Query and Earlier Nodes Unchanged (Priority: P1)

An operator uses `/query` or earlier `/ask` diagnosis stages and observes no behavior change from this repair.

**Why this priority**: The user explicitly scoped this work to the final `/ask` conclusion layer.

**Independent Test**: Run focused `/query` direct tests and ensure the new remediation-normalization helper is only called for non-query conclusion output.

**Acceptance Scenarios**:

1. **Given** layer is `QUERY`, **When** conclusion renders from `query_result`, **Then** remediation JSON normalization is not invoked.
2. **Given** layer/evidence/RCA nodes execute, **When** this feature is enabled, **Then** their structured-output behavior and prompts remain unchanged.

### Edge Cases

- The model emits malformed remediation JSON.
- The model emits `remediation_available=false` with basis that confirms finalizer evidence and prose patch advice.
- The model emits no remediation JSON at all but the final report and conclusion input both confirm the safe finalizer patch case.
- Multiple issue groups appear; this feature may normalize only the single confirmed finalizer group and must not invent actions for unrelated groups.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST keep previous work committed and pushed to `origin/qwen-before-architecture` before this feature's implementation changes.
- **FR-002**: The system MUST limit behavior changes to the `/ask` conclusion layer.
- **FR-003**: The system MUST NOT change `/query` routing, rendering, or structured extraction behavior.
- **FR-004**: The system MUST NOT change layer, evidence, or RCA node behavior for this feature.
- **FR-005**: The conclusion layer MUST continue to instruct the model to output a remediation JSON block in the prompt.
- **FR-006**: The conclusion layer MUST locally validate and normalize the final remediation JSON before returning the report.
- **FR-007**: When the final conclusion context confirms a TerminatingStuck Pod with current `deletionTimestamp` and non-empty finalizers, and the report includes finalizer patch advice but lacks structured actions, the system MUST produce a valid `remove_finalizer` structured action.
- **FR-008**: The normalized action MUST include dry-run, execute, and verify commands using real Pod name and namespace from evidence.
- **FR-009**: The system MUST NOT synthesize actions for force delete, placeholder targets, Pod NotFound, missing finalizers, historical-only events, or non-finalizer cases.
- **FR-010**: Normalized write actions MUST preserve existing review/auto semantics; they only provide structure for the existing safety review module.
- **FR-011**: If normalization cannot safely produce a valid action, the executor's existing invalid-plan or unavailable-plan behavior MUST remain intact.

### Key Entities *(include if feature involves data)*

- **Conclusion Remediation JSON**: The `## 🧩 结构化修复计划` JSON block embedded in the final Markdown report.
- **Safe Finalizer Evidence**: Current Pod evidence proving object existence, `deletionTimestamp`, namespace/name, and non-empty `metadata.finalizers`.
- **Normalized Remediation Action**: A local structured action with dry-run, execute, verify commands that passes existing remediation plan validation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Focused unit tests prove that a confirmed TerminatingStuck finalizer report with empty structured actions is normalized into a parseable `remove_finalizer` action.
- **SC-002**: Focused unit tests prove that force-delete advice or missing finalizer evidence does not create a structured write action.
- **SC-003**: Focused unit tests prove `/query` direct rendering tests still pass.
- **SC-004**: Real or near-real `/ask` validation shows a safe finalizer case reaches `remediation_approval_required` or produces a parseable structured plan ready for that existing path.

## Assumptions

- The existing executor and remediation safety review path already work when a valid structured plan is present.
- The first supported deterministic normalization case is confirmed TerminatingStuck finalizer removal because it is the user's concrete failure mode and has clear evidence requirements.
- Broader repair synthesis for ConfigMap, Secret, PVC, resources, or probe cases remains out of scope for this incremental repair.
