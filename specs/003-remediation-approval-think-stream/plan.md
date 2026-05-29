# Implementation Plan: Remediation Approval And Think Stream

**Branch**: `002-runbook-remediation-guidance` | **Date**: 2026-05-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-remediation-approval-think-stream/spec.md`

## Summary

Unify post-diagnosis remediation control under `workflow.remediation.enabled` and `workflow.remediation.mode`, remove `AUTO_REMEDIATE` and request-level `remediate=true` as execution gates, and make confirmed repairable cases produce stable structured remediation actions. If a repairable case still lacks actions, surface `invalid_plan` explicitly. In parallel, make streaming output adapt to LLM intermediate reasoning forms (`<think>`, provider reasoning fields, ordinary AI message reasoning) while preserving stable tool/progress/approval events.

The implementation should keep existing module boundaries: API routes normalize request behavior, workflow executor handles remediation stage selection and invalid-plan surfacing, remediation plan parsing validates the JSON contract, conclusion/report generation is responsible for stable structured plans, and service/AICall streaming handles think visibility.

## Technical Context

**Language/Version**: Python 3.10/3.12 compatible service code, Kubernetes YAML deployment manifests, Markdown documentation.

**Primary Dependencies**: FastAPI route handlers, LangChain agent streaming, OpenAI-compatible model transport, Kubernetes/MCP tools, existing remediation executor modules.

**Storage**: No persistent database changes. Runtime reports and context archives remain file-based under `/tmp/aiops/reports`; approval state remains in-memory as today.

**Testing**: Existing `pytest` unit tests under `tests/unit/**`, existing `python3 -m unittest` runbook tests under `test/workflow/**`, plus real Kubernetes deployment validation through `make delete build push deploy`.

**Target Platform**: Linux container deployed to Kubernetes through the existing manifests and NodePort service.

**Project Type**: Python web-service / Kubernetes AIOps agent.

**Performance Goals**: Remediation gating and invalid-plan validation must add negligible latency compared with LLM calls. Streaming progress should appear within 10 seconds of node activity when the node emits tokens, tool events, or heartbeat events.

**Constraints**:
- Do not execute write commands in review mode before human approval.
- Do not synthesize hidden chain-of-thought when the model/provider does not expose reasoning.
- Do not parse natural-language repair commands as a replacement for structured remediation actions.
- Preserve safe-command validation for auto mode.
- Preserve unrelated user changes in the working tree.

**Scale/Scope**:
- One post-diagnosis remediation flow.
- Existing `/ask` and `/query` streaming surfaces.
- Existing `deterministic` and `react` remediation executors.
- No new external service or persistent store.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. 高内聚低耦合**: PASS. Plan keeps request semantics, workflow execution, remediation contract parsing, report generation, and streaming rendering in their existing modules.
- **II. 证据优先与可验证**: PASS. Repair actions still require current evidence, structured plan basis, safe-command validation, approval or auto mode, and post-action verification.
- **III. 测试先行**: PASS. Tasks must start with failing tests for removed gates, stable actions, invalid-plan surfacing, and think visibility.
- **IV. 安全修复优先**: PASS. Review mode requires approval before every write action; auto mode remains bounded by safe-command validation and verification.
- **V. 最小可用变更**: PASS. No new service, database, or broad refactor is required.

## Project Structure

### Documentation (this feature)

```text
specs/003-remediation-approval-think-stream/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── remediation-stream-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
app/
├── api/
│   └── routes.py                         # request-level remediation parameter cleanup
├── core/
│   ├── aicall/
│   │   ├── builtin_tools.py              # remove AUTO_REMEDIATE semantics if still active
│   │   └── client.py                     # reasoning extraction / streaming event source
│   ├── remediation/
│   │   ├── agent.py                      # review/auto approval behavior remains bounded
│   │   ├── executor.py                   # deterministic approval behavior
│   │   └── plans.py                      # structured plan validation
│   ├── service.py                        # text/SSE think stream rendering
│   └── workflow/
│       ├── executor.py                   # remediation stage gating and invalid_plan surfacing
│       └── nodes/
│           ├── base.py                   # remove AUTO_REMEDIATE prompt policy
│           └── conclusion_formatter.py   # stable structured remediation plan generation
deploy/
├── configmap/config.yaml                 # canonical remediation mode docs/config
├── k8s-simple.yaml                       # remove AUTO_REMEDIATE env wiring
└── secrets/core.yaml                     # remove AUTO_REMEDIATE secret key
docs/
├── remediation-usage.md                  # update usage semantics
└── GUIDE.md                              # remove AUTO_REMEDIATE as control
tests/
└── unit/
    ├── api/
    ├── aicall/
    ├── remediation/
    └── workflow/
```

**Structure Decision**: Use the existing single-service layout. Do not introduce a new remediation gateway or streaming subsystem; extend the current contracts at their existing ownership points.

## Complexity Tracking

No constitution violations or added architectural complexity.
