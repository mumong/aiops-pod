# Implementation Plan: Ask Conclusion Remediation JSON

**Branch**: `005-ask-conclusion-remediation-json` | **Date**: 2026-06-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-ask-conclusion-remediation-json/spec.md`

## Summary

Stabilize the final `/ask` conclusion remediation JSON so a confirmed safe finalizer repair enters the existing safety review path. Keep `/query`, layer, evidence, and RCA unchanged. The conclusion node will keep prompting for JSON, then locally validate and normalize the remediation plan before returning the final report.

## Technical Context

**Language/Version**: Python 3.x

**Primary Dependencies**: Existing workflow nodes, remediation plan parser, pytest

**Storage**: No persistent schema change

**Testing**: pytest focused unit tests plus near-real workflow executor validation

**Target Platform**: Kubernetes deployment running `aiops-copilot`

**Project Type**: Python web service / workflow agent

**Performance Goals**: No additional LLM calls; normalization must be local string/JSON processing in conclusion.

**Constraints**: `/ask` only; conclusion only; no `/query`, layer, evidence, RCA changes; no new remediation execution mode.

**Scale/Scope**: Single confirmed finalizer-removal normalization case plus safety regressions.

## Constitution Check

- **I. 高内聚低耦合**: PASS. The change remains in the conclusion node and reuses the existing remediation parser contract.
- **II. 证据优先与可验证**: PASS. Normalization requires current Pod deletionTimestamp and finalizers evidence.
- **III. 测试先行**: PASS. Add failing conclusion-level tests before implementation and run focused suites.
- **IV. 安全修复优先**: PASS. Only standard finalizer patch is synthesized, never force delete.
- **V. 最小可用变更**: PASS. No new node, executor gate, or query behavior change.

## Project Structure

### Documentation (this feature)

```text
specs/005-ask-conclusion-remediation-json/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/remediation-json-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
app/core/workflow/nodes/
└── conclusion_formatter.py

tests/unit/workflow/
├── test_ask_conclusion_remediation_json.py
├── test_query_direct_mode.py
└── test_remediation_plan_handling.py
```

**Structure Decision**: Use the existing conclusion node boundary because the feature is final-report remediation-plan normalization. Reuse `extract_remediation_plan` for validation.

## Complexity Tracking

No constitution violations.
