# Implementation Plan: Runbook Remediation Guidance

**Branch**: `002-runbook-remediation-guidance` | **Date**: 2026-05-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-runbook-remediation-guidance/spec.md`

## Summary

Update the active Kubernetes Pod abnormal-status runbooks with compact, branch-specific
standard remediation guidance. Preserve the current active runbook ConfigMap outside
the deployment directory, add automated validation for the new guidance and unsafe
ordering, bump the release to `11.0.0`, and validate with the real build/deploy/query
path.

## Technical Context

**Language/Version**: Python 3.x for validation tests; YAML/Markdown embedded in Kubernetes ConfigMap

**Primary Dependencies**: Standard library `unittest`, `pathlib`, `re`; existing Makefile, Docker, kubectl

**Storage**: File-based repository artifacts (`deploy/configmap/runbooks.yaml`, `docs/runbooks-backups/`)

**Testing**: `python3 -m unittest` focused tests plus real Kubernetes deployment validation

**Target Platform**: Linux server workspace deploying to Kubernetes namespace `aiops`

**Project Type**: Python web service with Kubernetes deployment assets and ConfigMap-based runbooks

**Performance Goals**: No runtime performance impact; prompt-context growth stays bounded by concise sections

**Constraints**: Preserve unrelated working-tree changes; backups must not live under `deploy/`; destructive repairs must be fallbacks only

**Scale/Scope**: 10 active Pod abnormal-status runbooks in `deploy/configmap/runbooks.yaml`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **高内聚低耦合**: PASS. Runbook content, backup docs, tests, and versioning remain separate files.
- **证据优先与可验证**: PASS. Guidance is branch-specific and validation includes real `/ask`.
- **测试先行**: PASS. Add failing runbook validation test before editing active runbooks.
- **安全修复优先**: PASS. Standard sections prioritize reversible/scoped actions before force deletion.
- **最小可用变更**: PASS. Only active runbooks, backup docs, focused test, version and deployment image are touched.

## Project Structure

### Documentation (this feature)

```text
specs/002-runbook-remediation-guidance/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
deploy/configmap/
└── runbooks.yaml

docs/runbooks-backups/
└── runbooks-2026-05-29-before-remediation-guidance.yaml

test/workflow/
└── test_runbook_remediation_guidance.py

VERSION
deploy/k8s-simple.yaml
```

**Structure Decision**: Keep the feature as a content-and-validation change. No runtime code
path needs a new abstraction because runbooks are already consumed from the active ConfigMap.

## Complexity Tracking

No constitution violations.
