# Implementation Plan: Ask Layer Structured Fallback

**Branch**: `006-ask-layer-structured-fallback` | **Date**: 2026-06-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-ask-layer-structured-fallback/spec.md`

## Summary

Stabilize `/ask` layer classification by distinguishing LLM connectivity failure from schema extraction failure, enabling validated JSON text fallback for layer extraction when native structured output is unsupported, and preserving the `/query` direct path.

## Technical Context

**Language/Version**: Python 3.x

**Primary Dependencies**: FastAPI workflow service, LangGraph/LangChain AICall wrapper, Pydantic, pytest

**Storage**: Context archive files under `/tmp/aiops/reports/context_archives`; no persistent schema change

**Testing**: pytest focused unit tests plus real deployed `/ask` validation with backend logs

**Target Platform**: Kubernetes deployment running `aiops-copilot`

**Project Type**: Python web service / workflow agent

**Performance Goals**: Avoid duplicate layer extraction attempts when LLM connectivity is clearly unavailable; do not add `/query` latency.

**Constraints**: `/ask` layer-only behavior change; no remediation approval semantic changes; no `/query` direct regression.

**Scale/Scope**: Layer classifier structured finalization and error reporting.

## Constitution Check

- **I. 高内聚低耦合**: PASS. Changes stay in the layer classifier and its focused tests.
- **II. 证据优先与可验证**: PASS. Clear LLM-unavailable errors are based on observed connection failure signals; no fake diagnosis is generated.
- **III. 测试先行**: PASS. Add failing tests before implementation.
- **IV. 安全修复优先**: PASS. Does not execute remediation or change approval mode.
- **V. 最小可用变更**: PASS. Only the `/ask` layer structured extraction failure path is changed.

## Project Structure

### Documentation (this feature)

```text
specs/006-ask-layer-structured-fallback/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/layer-fallback-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
app/core/workflow/nodes/
└── layer_classifier.py

tests/unit/workflow/
└── test_fast_paths.py
```

**Structure Decision**: Use the existing layer classifier boundary. Do not add new services because the required behavior is local to layer extraction and error handling.

## Complexity Tracking

No constitution violations.
