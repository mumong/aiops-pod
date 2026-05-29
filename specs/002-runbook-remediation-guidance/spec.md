# Feature Specification: Runbook Remediation Guidance

**Feature Branch**: `002-runbook-remediation-guidance`

**Created**: 2026-05-29

**Status**: Draft

**Input**: User description: "梳理现有 Kubernetes Pod 异常 runbooks，为常见状态和细分 case 增加标准、安全、简洁的修复建议，避免 agent 在 finalizer 等场景中过早推荐 delete --force；保留当前 runbooks 作为备份；版本从 11.0.0 开始并进行真实部署测试。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agent Gets Safe Case-Specific Repairs (Priority: P1)

As an operator asking `/ask` for a Pod abnormal-status diagnosis, I want the selected runbook to tell the agent the safest standard remediation for the confirmed branch, so the final repair proposal is not a generic or destructive command.

**Why this priority**: This directly addresses the observed Terminating/finalizer problem and reduces unsafe repair plans.

**Independent Test**: Query a real TerminatingStuck scenario after deployment and verify the answer recommends finalizer patch only when finalizers are confirmed, and does not jump directly to `delete --force`.

**Acceptance Scenarios**:

1. **Given** a Terminating Pod with `metadata.deletionTimestamp` and non-empty `metadata.finalizers`, **When** the agent reads `pod-terminating-stuck.md`, **Then** it can recommend a scoped `kubectl patch pod ... '{"metadata":{"finalizers":null}}' --type=merge` remediation with prerequisite and verification notes.
2. **Given** a Terminating Pod with `finalizers: <none>`, **When** the agent reads the same runbook, **Then** it must exclude finalizer cleanup and evaluate node/kubelet, volume, or grace-period branches before any force delete fallback.

---

### User Story 2 - Runbooks Stay Compact And Actionable (Priority: P2)

As a maintainer, I want every active Pod abnormal-status runbook to gain concise remediation guidance without becoming a long tutorial, so future edits remain easy to review and the model receives clear decision signals.

**Why this priority**: The runbooks are prompt context; excessive text increases cost and can dilute the branch-specific rules.

**Independent Test**: Parse the active runbooks and verify each targeted runbook contains a standard remediation section with branch-specific bullets and explicit unsafe-fallback wording where applicable.

**Acceptance Scenarios**:

1. **Given** the current active runbook ConfigMap, **When** the update is applied, **Then** each Pod abnormal-status runbook contains a `## 标准修复建议` section.
2. **Given** a branch has multiple remediation options, **When** the section is read, **Then** the safest standard action appears before destructive fallback actions.

---

### User Story 3 - Current Runbooks Are Preserved Before Editing (Priority: P3)

As a maintainer, I want the pre-change active runbook file preserved outside the deployment directory, so I can compare or restore content without risking Kubernetes applying the backup as the active ConfigMap.

**Why this priority**: The user explicitly requested a backup, and backups inside `deploy/` can be applied by `make deploy --recursive`.

**Independent Test**: Confirm a timestamped backup exists outside `deploy/` and matches the pre-change `deploy/configmap/runbooks.yaml` content.

**Acceptance Scenarios**:

1. **Given** the repository before runbook edits, **When** the feature starts implementation, **Then** the active `deploy/configmap/runbooks.yaml` is copied to `docs/runbooks-backups/`.
2. **Given** `make deploy` applies `deploy/` recursively, **When** backup files are created, **Then** they must not live under `deploy/`.

### Edge Cases

- A runbook describes a historical or already-resolved symptom; remediation guidance must tell the agent not to repair against stale evidence.
- A repair is potentially destructive, such as force deletion, finalizer removal, or storage cleanup; the guidance must require confirmed current evidence and describe safer alternatives first.
- Multiple runbook branches match partially; the guidance must prefer branch-specific evidence over generic Kubernetes advice.
- The real cluster scenario may already be cleaned up; validation must still inspect deployed runbook content and the actual `/ask` answer or archive from the new version.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST preserve the current active `deploy/configmap/runbooks.yaml` as a backup outside `deploy/` before modifying active runbook content.
- **FR-002**: The active Pod abnormal-status runbooks MUST include concise `## 标准修复建议` sections for confirmed common branches.
- **FR-003**: The TerminatingStuck runbook MUST prioritize finalizer patch remediation for confirmed non-empty finalizers and MUST mark force delete as an emergency fallback after branch checks.
- **FR-004**: Each remediation recommendation MUST include a verification command or observable success condition.
- **FR-005**: Remediation guidance MUST explicitly state branch exclusions, such as not recommending finalizer cleanup when finalizers are empty.
- **FR-006**: Runbook edits MUST remain diagnostic-guide oriented and avoid long generic tutorials.
- **FR-007**: The implementation MUST include automated validation that detects missing remediation sections and unsafe ordering for the TerminatingStuck finalizer case.
- **FR-008**: The release version MUST be set to `11.0.0` for real deployment validation.
- **FR-009**: Real validation MUST run the repository deployment path (`make delete`, `make build`, `make push`, `make deploy`) and a real `/ask` query against the deployed service, unless infrastructure prevents it and the exact blocker is recorded.

### Key Entities *(include if feature involves data)*

- **Runbook**: A markdown document embedded in the active Kubernetes ConfigMap under `deploy/configmap/runbooks.yaml`.
- **Remediation Branch**: A confirmed root-cause case within a runbook, with prerequisites, recommended action, fallback, and verification.
- **Runbook Backup**: A copy of the active runbook ConfigMap stored outside deployment-applied directories.
- **Real Validation Run**: A versioned build/deploy/query cycle used to verify model-facing runbook behavior in the live service.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 11 active Pod abnormal-status runbooks contain `## 标准修复建议` after the update.
- **SC-002**: Automated tests fail on the pre-change runbooks and pass after remediation guidance is added.
- **SC-003**: In a real TerminatingStuck `/ask` run, the answer references the updated runbook guidance and avoids first-line `delete --force` for the finalizer case.
- **SC-004**: The deployed image tag is `xnet.registry.io:8443/xnet-cloud/aiops-copilot:11.0.0` after validation.

## Assumptions

- The scope is the active Pod abnormal-status runbooks in `deploy/configmap/runbooks.yaml`; the PromQL reference runbook is out of scope.
- The backup should be kept in documentation space, not in `deploy/`, to avoid ConfigMap overwrite risk during recursive deploy.
- Existing remediation execution safety gates remain unchanged; this feature updates model reference guidance and validation around it.
- The real cluster and registry used by prior validation remain available from this workspace.
