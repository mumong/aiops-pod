# Implementation Plan: Query Direct Render

**Branch**: `004-query-direct-render` | **Date**: 2026-06-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-query-direct-render/spec.md`

## Summary

Restore the fast `/query` direct path by extracting query structure from the first LLM/tool collection loop as JSON text or real Prometheus tool events, then rendering the final answer locally. The change must be gated to `query_mode=direct` and must not alter `/ask` diagnosis, diagnosis conclusion, or remediation approval behavior.

## Technical Context

**Language/Version**: Python 3.x

**Primary Dependencies**: FastAPI workflow service, LangGraph/LangChain AICall wrapper, pytest

**Storage**: Context archive files under `/tmp/aiops/reports/context_archives`; no persistent schema change

**Testing**: pytest focused unit tests plus real `/query` deployment validation

**Target Platform**: Kubernetes deployment running `aiops-copilot`

**Project Type**: Python web service / workflow agent

**Performance Goals**: Successful CPU/memory `/query` should avoid the extra layer_extract/conclusion LLM latency and complete near the historical 1 minute target when external tools are responsive.

**Constraints**: Query-only changes; no `/ask` regression; no Pydantic `call_structured` dependency for query direct extraction; no raw transcript fallback when structured query data exists.

**Scale/Scope**: `/query` direct workflow with layer and conclusion nodes.

## Constitution Check

- **I. 高内聚低耦合**: PASS. Query extraction/rendering remains in query-gated workflow nodes.
- **II. 证据优先与可验证**: PASS. QueryResult is based on real LLM JSON or real tool events, with missing reasons when data is absent.
- **III. 测试先行**: PASS. Add failing unit tests before code changes and run real `/query` validation.
- **IV. 安全修复优先**: PASS. Query path is read-only and does not execute remediation.
- **V. 最小可用变更**: PASS. Change only query direct classification/rendering and focused tests.

## Project Structure

### Documentation (this feature)

```text
specs/004-query-direct-render/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/query-direct-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
app/core/workflow/nodes/
├── layer_classifier.py
└── conclusion_formatter.py

tests/unit/workflow/
├── test_query_direct_mode.py
└── test_fast_paths.py
```

**Structure Decision**: Use existing workflow node boundaries. Do not introduce a new service abstraction unless tests show duplication or coupling becomes unsafe.

## Complexity Tracking

No constitution violations.
