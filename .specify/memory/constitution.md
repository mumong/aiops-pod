<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- [PRINCIPLE_1_NAME] -> I. 高内聚低耦合
- [PRINCIPLE_2_NAME] -> II. 证据优先与可验证
- [PRINCIPLE_3_NAME] -> III. 测试先行
- [PRINCIPLE_4_NAME] -> IV. 安全修复优先
- [PRINCIPLE_5_NAME] -> V. 最小可用变更
Added sections:
- Runbook 与诊断治理
- 交付工作流
Removed sections: none
Templates requiring updates:
- ✅ .specify/templates/plan-template.md: Constitution Check section already supports project gates
- ✅ .specify/templates/spec-template.md: requirements and success criteria already support testable outcomes
- ✅ .specify/templates/tasks-template.md: task format already supports TDD and validation tasks
Follow-up TODOs: none
-->
# Robusta AIOps Copilot Constitution

## Core Principles

### I. 高内聚低耦合
Every change MUST keep responsibilities bounded. Diagnostic prompts, runbook content,
workflow state, remediation execution, deployment config, and tests MUST remain
separate unless there is a documented reason to couple them. A module or document
section SHOULD have one clear purpose, one primary consumer, and minimal knowledge
of unrelated flows.

### II. 证据优先与可验证
All diagnosis and remediation guidance MUST be grounded in current, observable
cluster evidence. Historical Events, stale reports, or generic failure patterns
MUST NOT be presented as current root cause unless the runbook explicitly labels
them as historical or exclusion evidence. Any feature claiming behavior improvement
MUST include an automated or real-environment verification path.

### III. 测试先行
Behavior changes MUST start with a failing automated test or a documented
pre-change real-environment reproduction. Tests MUST validate user-visible
outcomes, not only implementation details. A change is not complete until the
relevant focused tests and the agreed real validation path have been run and the
results are recorded.

### IV. 安全修复优先
Runbooks and remediation logic MUST prefer reversible, scoped, standard Kubernetes
operations before destructive shortcuts. Force deletion, finalizer removal, node
restart, or data-affecting storage actions MUST be described as conditional
fallbacks with prerequisites, risk notes, and post-action verification. The agent
MUST not recommend a write operation unless the required evidence branch has been
confirmed.

### V. 最小可用变更
Changes MUST be as small as possible while satisfying the feature. Runbooks SHOULD
stay concise: add decision-ready remediation guidance for common confirmed cases,
but do not turn diagnostic manuals into long tutorials. New abstractions,
documents, and tests MUST serve a concrete requirement.

## Runbook 与诊断治理

Runbooks are operator reference material for `/ask` diagnosis and repair planning.
Each Pod abnormal-status runbook MUST define: current-state recognition, critical
evidence, root-cause branches, standard or safest recommended remediation for
confirmed branches, unsafe fallbacks, and verification commands. Remediation
guidance MUST be branch-specific: if evidence excludes a branch, the runbook MUST
tell the agent not to recommend that branch's repair.

Runbook backups MUST be stored outside deployment-applied directories so they
cannot accidentally overwrite active ConfigMaps during `make deploy`.

## 交付工作流

Feature work MUST follow spec -> plan -> tasks -> implementation -> verification.
Implementation MUST preserve unrelated user changes in the working tree. Versioned
deployment validation MUST update `VERSION`, build and push the image, deploy it,
wait for the Pod rollout, then run a real `/ask` scenario and inspect the observed
output or archived evidence.

## Governance

This constitution supersedes ad hoc implementation habits for this repository.
Amendments require updating this file, explaining the version bump, and checking
the spec, plan, and task templates for alignment. Versioning follows semantic
governance: MAJOR for incompatible governance changes, MINOR for new principles
or materially expanded requirements, PATCH for wording-only clarifications.

Every implementation plan MUST include a Constitution Check. Any violation must
be explicitly justified and paired with a simpler alternative that was rejected.
Reviewers and agents MUST block completion claims until verification evidence is
available.

**Version**: 1.0.0 | **Ratified**: 2026-05-29 | **Last Amended**: 2026-05-29
