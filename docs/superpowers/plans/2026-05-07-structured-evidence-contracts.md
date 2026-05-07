# Structured Evidence Contracts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make evidence planning and plan/tool matching type-safe with Pydantic contracts while preserving the existing tool-calling agent loop.

**Architecture:** Add focused Pydantic schemas for evidence plan and match adjudication. Add `AICall.call_structured()` as a provider-compatible wrapper that prefers LangChain structured output and falls back to JSON parsing plus Pydantic validation. Wire evidence plan parsing and match adjudication through these schemas, keeping existing rule fallback when structured calls are unavailable.

**Tech Stack:** Python 3.12, Pydantic 2.12, LangChain 1.1, LangGraph 1.0, pytest.

---

### Task 1: Evidence Contract Schemas

**Files:**
- Create: `app/core/workflow/schemas.py`
- Test: `tests/unit/workflow/test_structured_schemas.py`

- [ ] **Step 1: Write failing schema validation tests**

```python
import pytest
from pydantic import ValidationError

from app.core.workflow.schemas import (
    EvidenceMatchOutput,
    EvidencePlanOutput,
)


def test_evidence_plan_output_validates_required_fields():
    parsed = EvidencePlanOutput.model_validate({
        "layer": "L3",
        "evidence_plan": [
            {
                "id": "e1",
                "description": "获取 Pod 事件",
                "level": "critical",
                "tool": "kubectl_events",
                "command": "kubectl get events -n aaa",
                "purpose": "确认镜像拉取失败原因",
            }
        ],
        "collection_strategy": "先确认当前异常 Pod，再验证事件。",
    })

    assert parsed.evidence_plan[0].id == "e1"
    assert parsed.evidence_plan[0].level == "critical"


def test_evidence_plan_output_rejects_missing_command():
    with pytest.raises(ValidationError):
        EvidencePlanOutput.model_validate({
            "layer": "L3",
            "evidence_plan": [
                {
                    "id": "e1",
                    "description": "获取 Pod 事件",
                    "level": "critical",
                    "tool": "kubectl_events",
                    "purpose": "确认镜像拉取失败原因",
                }
            ],
            "collection_strategy": "先确认当前异常 Pod。",
        })


def test_evidence_match_output_validates_match_decisions():
    parsed = EvidenceMatchOutput.model_validate({
        "matches": [
            {
                "plan_id": "e1",
                "tool_result_index": 0,
                "matched": True,
                "confidence": 0.91,
                "reason": "对象、namespace、工具意图一致",
            },
            {
                "plan_id": "e2",
                "tool_result_index": None,
                "matched": False,
                "confidence": 0.93,
                "reason": "计划查询 NetworkPolicy，但结果是 Secret 表",
            },
        ],
        "unmatched_plan_ids": ["e2"],
        "unplanned_tool_result_indexes": [3],
    })

    assert parsed.matches[0].matched is True
    assert parsed.matches[1].tool_result_index is None
```

- [ ] **Step 2: Run schema tests and verify they fail**

Run: `.venv/bin/python -m pytest tests/unit/workflow/test_structured_schemas.py -q`

Expected: FAIL because `app.core.workflow.schemas` does not exist.

- [ ] **Step 3: Add minimal Pydantic schema implementation**

```python
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


EvidenceLevelName = Literal["critical", "important", "optional", "reference"]


class EvidencePlanItem(BaseModel):
    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    level: EvidenceLevelName = "important"
    tool: str = Field(min_length=1)
    command: str = Field(min_length=1)
    purpose: str = Field(default="")


class EvidencePlanOutput(BaseModel):
    layer: str = Field(default="")
    evidence_plan: list[EvidencePlanItem] = Field(default_factory=list)
    collection_strategy: str = Field(default="")


class ToolObservationCandidate(BaseModel):
    index: int
    tool_name: str
    tool_args: dict[str, Any] = Field(default_factory=dict)
    structured: dict[str, Any] = Field(default_factory=dict)
    result_preview: str = ""
    raw_ref: str | None = None
    summary_ref: str | None = None
    structured_ref: str | None = None


class EvidenceMatchItem(BaseModel):
    plan_id: str = Field(min_length=1)
    tool_result_index: int | None = None
    matched: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = ""


class EvidenceMatchOutput(BaseModel):
    matches: list[EvidenceMatchItem] = Field(default_factory=list)
    unmatched_plan_ids: list[str] = Field(default_factory=list)
    unplanned_tool_result_indexes: list[int] = Field(default_factory=list)
```

- [ ] **Step 4: Run schema tests and verify they pass**

Run: `.venv/bin/python -m pytest tests/unit/workflow/test_structured_schemas.py -q`

Expected: PASS.

### Task 2: AICall Structured Output Wrapper

**Files:**
- Modify: `app/core/aicall/client.py`
- Test: `tests/unit/aicall/test_event_loop_safety.py`

- [ ] **Step 1: Write failing `call_structured` fallback test**

Add a test that monkeypatches `call_simple` to return fenced JSON and asserts `call_structured(..., EvidencePlanOutput)` returns a Pydantic object.

- [ ] **Step 2: Run targeted test and verify it fails**

Run: `.venv/bin/python -m pytest tests/unit/aicall/test_event_loop_safety.py::test_call_structured_validates_pydantic_schema_from_json_fallback -q`

Expected: FAIL because `AICall.call_structured` does not exist.

- [ ] **Step 3: Implement minimal `call_structured`**

Implementation requirements:
- Accept `schema: type[BaseModel]`.
- Try `self.call_simple(...)`, parse with `extract_json_payload`, validate with `schema.model_validate`.
- Return `(model_instance_or_none, raw_text)`.
- Log validation failures and return `(None, raw_text)`.
- Do not change existing `call_simple_json` behavior.

- [ ] **Step 4: Run AICall tests**

Run: `.venv/bin/python -m pytest tests/unit/aicall/test_event_loop_safety.py -q`

Expected: PASS.

### Task 3: Evidence Plan Structured Validation

**Files:**
- Modify: `app/core/workflow/nodes/evidence_collector.py`
- Test: `tests/unit/workflow/test_evidence_dynamic_stop.py`

- [ ] **Step 1: Write failing structured plan parsing test**

Add a fake `ai_call.call_structured` returning `EvidencePlanOutput` and assert `_plan_evidence_with_llm()` uses it when available.

- [ ] **Step 2: Implement structured plan call path**

Implementation requirements:
- Keep the existing agent/tool loop.
- After the loop, parse `evidence_plan` from thinking events as today.
- Validate the extracted dict/list with `EvidencePlanOutput`.
- If invalid, fall back to existing parser and retry logic.
- Preserve `evidence_plan` as `list[dict]` for existing downstream code.

- [ ] **Step 3: Run evidence dynamic stop tests**

Run: `.venv/bin/python -m pytest tests/unit/workflow/test_evidence_dynamic_stop.py -q`

Expected: PASS.

### Task 4: Evidence Match Structured Validation

**Files:**
- Modify: `app/core/workflow/nodes/evidence_collector.py`
- Test: `tests/unit/workflow/test_evidence_dynamic_stop.py`

- [ ] **Step 1: Write failing structured match adjudicator test**

Add a fake `ai_call.call_structured` returning `EvidenceMatchOutput` and assert `_adjudicate_plan_tool_matches()` accepts matching decisions and rejects explicit non-matches.

- [ ] **Step 2: Replace raw `call_simple_json` match adjudication with `call_structured`**

Implementation requirements:
- Use `EvidenceMatchOutput` schema.
- Preserve current injected `plan_match_adjudicator` for tests.
- Preserve rule fallback when no `ai_call` exists or structured validation fails.
- Keep QUERY mode disabled for adjudication.

- [ ] **Step 3: Run workflow tests**

Run: `.venv/bin/python -m pytest tests/unit/workflow/test_evidence_dynamic_stop.py tests/unit/workflow/test_fast_paths.py -q`

Expected: PASS.

### Task 5: Focused Regression Run

**Files:**
- No new files.

- [ ] **Step 1: Run focused regression suite**

Run:

```bash
.venv/bin/python -m pytest \
  tests/unit/aicall/test_event_loop_safety.py \
  tests/unit/aicall/test_observation_processing.py \
  tests/unit/workflow/test_evidence_dynamic_stop.py \
  tests/unit/workflow/test_fast_paths.py \
  -q
```

Expected: PASS.

- [ ] **Step 2: Document known unrelated failures**

If broader tests still show `test_rca_blocks_current_root_cause_when_primary_pod_is_missing` failing, record it as unrelated to structured evidence contracts. Do not mix RCA behavior changes into this implementation.

