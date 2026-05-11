# Structured Agent Runtime Convergence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Converge workflow LLM calls onto one low-coupling structured runtime so layer, evidence, RCA, and conclusion all use Pydantic response schemas as the sole structured output boundary.

**Architecture:** Add a focused `StructuredAgentRuntime` abstraction that owns `create_agent(response_format=...)` invocation, schema validation, and fallback policy. Nodes declare schema and tool requirements, then consume typed results; deterministic completeness/statistics remain code-owned and are never trusted from LLM text. This keeps node business logic high-cohesion while reducing duplicated structured-call plumbing.

**Tech Stack:** Python 3.12, Pydantic v2, LangChain 1.1 `create_agent(response_format=ToolStrategy)`, LangGraph workflow nodes, pytest.

---

## File Structure

- Create `app/core/workflow/structured_runtime.py`: node-agnostic runtime wrapper for structured agent calls and structured response extraction.
- Modify `app/core/aicall/client.py`: support `response_schema` with no real tools by still using `create_agent(response_format=...)`.
- Modify `app/core/workflow/nodes/base.py`: expose `_call_structured_agent()` helper that all nodes can use.
- Modify `app/core/workflow/schemas.py`: add `ConclusionOutput`.
- Modify `app/core/workflow/nodes/root_cause_analyzer.py`: replace direct `call_structured()` node output path with `_call_structured_agent(..., RCAOutput, tools=[])`.
- Modify `app/core/workflow/nodes/conclusion_formatter.py`: generate `ConclusionOutput` via `_call_structured_agent(..., ConclusionOutput, tools=[])`, then render `markdown_report`.
- Modify `app/core/workflow/nodes/layer_classifier.py`: remove local structured response extraction duplication and use runtime extraction helper.
- Modify `app/core/workflow/nodes/evidence_collector.py`: remove local structured response extraction duplication and use runtime extraction helper.
- Modify `deploy/configmap/config.yaml`: replace node-specific flags with a consistent `structured_runtime` section while keeping old flags as compatibility aliases.
- Test files:
  - `tests/unit/workflow/test_structured_runtime.py`
  - `tests/unit/aicall/test_event_loop_safety.py`
  - `tests/unit/workflow/test_context_handoff.py`
  - `tests/unit/workflow/test_fast_paths.py`
  - `tests/unit/workflow/test_evidence_dynamic_stop.py`

## Task 1: Runtime Extraction Unit

**Files:**
- Create: `app/core/workflow/structured_runtime.py`
- Test: `tests/unit/workflow/test_structured_runtime.py`

- [ ] **Step 1: Write failing tests for schema extraction**

```python
from pydantic import BaseModel

from app.core.workflow.structured_runtime import StructuredAgentRuntime


class DemoOutput(BaseModel):
    value: str


def test_extract_structured_response_accepts_pydantic_instance():
    response = type("Response", (), {"structured_response": DemoOutput(value="ok")})()

    parsed = StructuredAgentRuntime.extract_structured_response(response, DemoOutput)

    assert parsed == DemoOutput(value="ok")


def test_extract_structured_response_accepts_dict():
    response = type("Response", (), {"structured_response": {"value": "ok"}})()

    parsed = StructuredAgentRuntime.extract_structured_response(response, DemoOutput)

    assert parsed == DemoOutput(value="ok")


def test_extract_structured_response_returns_none_when_missing():
    response = type("Response", (), {"result": "text only"})()

    parsed = StructuredAgentRuntime.extract_structured_response(response, DemoOutput)

    assert parsed is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest -q tests/unit/workflow/test_structured_runtime.py`

Expected: FAIL because `app.core.workflow.structured_runtime` does not exist.

- [ ] **Step 3: Implement minimal runtime extraction**

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, TypeVar

from pydantic import BaseModel

SchemaT = TypeVar("SchemaT", bound=BaseModel)


@dataclass(frozen=True)
class StructuredAgentSpec:
    node_id: str
    output_schema: type[BaseModel]
    use_tools: bool = True
    allow_fallback: bool = True


class StructuredAgentRuntime:
    @staticmethod
    def extract_structured_response(response: Any, schema: type[SchemaT]) -> Optional[SchemaT]:
        structured = getattr(response, "structured_response", None)
        if structured is None:
            return None
        if isinstance(structured, schema):
            return structured
        if isinstance(structured, dict):
            return schema.model_validate(structured)
        if hasattr(structured, "model_dump"):
            return schema.model_validate(structured.model_dump())
        return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest -q tests/unit/workflow/test_structured_runtime.py`

Expected: PASS.

## Task 2: AICall Supports Structured Agent Without Real Tools

**Files:**
- Modify: `app/core/aicall/client.py`
- Test: `tests/unit/aicall/test_event_loop_safety.py`

- [ ] **Step 1: Write failing test**

Add a test proving `AICall.call(..., tools=[], response_schema=DemoOutput)` uses `create_agent(response_format=...)` instead of `call_simple()`.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest -q tests/unit/aicall/test_event_loop_safety.py::test_call_without_real_tools_can_use_agent_structured_response`

Expected: FAIL because no-tools currently short-circuits to `call_simple()`.

- [ ] **Step 3: Implement minimal change**

Change the no-tools short-circuit in `AICall.call()` to apply only when `response_schema is None`. When `response_schema` is present, proceed into `create_agent` with `tools=[]`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest -q tests/unit/aicall/test_event_loop_safety.py::test_call_without_real_tools_can_use_agent_structured_response`

Expected: PASS.

## Task 3: WorkflowNode Structured Agent Helper

**Files:**
- Modify: `app/core/workflow/nodes/base.py`
- Test: `tests/unit/workflow/test_structured_runtime.py`

- [ ] **Step 1: Write failing test**

Add a minimal fake `WorkflowNode` subclass and fake `_call_llm()` response; assert `_call_structured_agent(question, prompt, schema, use_tools=False)` returns the Pydantic object and thinking events.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest -q tests/unit/workflow/test_structured_runtime.py`

Expected: FAIL because `_call_structured_agent` does not exist.

- [ ] **Step 3: Implement helper**

Add helper to `WorkflowNode`:

```python
def _call_structured_agent(self, question, system_prompt, schema, *, use_tools=True, stop_checker=None, **kwargs):
    response, events = self._call_llm(
        question,
        system_prompt,
        stop_checker=stop_checker,
        response_schema=schema,
        force_no_tools=not use_tools,
        **kwargs,
    )
    parsed = StructuredAgentRuntime.extract_structured_response(response, schema)
    return parsed, response, events
```

The helper should be the only node-level method that knows `response_schema`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest -q tests/unit/workflow/test_structured_runtime.py`

Expected: PASS.

## Task 4: Tool Selection Support

**Files:**
- Modify: `app/core/workflow/nodes/base.py`
- Modify: `app/core/aicall/client.py`
- Test: `tests/unit/workflow/test_structured_runtime.py`

- [ ] **Step 1: Write failing test**

Test that `_call_structured_agent(..., use_tools=False)` passes an empty tool list to `AICall.call()` through `_call_llm`.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest -q tests/unit/workflow/test_structured_runtime.py`

Expected: FAIL because `_call_llm()` always uses `self.tools`.

- [ ] **Step 3: Implement `force_no_tools`**

In `_call_llm()`, pop `force_no_tools = kwargs.pop("force_no_tools", False)` and use:

```python
tools = [] if force_no_tools else (getattr(self, "tools", []) or [])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest -q tests/unit/workflow/test_structured_runtime.py`

Expected: PASS.

## Task 5: RCA Uses Unified Runtime

**Files:**
- Modify: `app/core/workflow/nodes/root_cause_analyzer.py`
- Test: `tests/unit/workflow/test_context_handoff.py`

- [ ] **Step 1: Write failing test**

Add a test asserting RCA lite calls `_call_structured_agent(..., RCAOutput, use_tools=False)` and does not call `ai_call.call_structured()`.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest -q tests/unit/workflow/test_context_handoff.py::test_rca_lite_uses_structured_agent_runtime`

Expected: FAIL because RCA currently calls `ai_call.call_structured()` directly.

- [ ] **Step 3: Replace RCA lite implementation**

Use:

```python
structured, response, events = self._call_structured_agent(
    question=user_message,
    system_prompt=system_prompt,
    schema=RCAOutput,
    use_tools=False,
)
```

Return `structured.model_dump()` when present; keep existing low-confidence fallback when absent.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest -q tests/unit/workflow/test_context_handoff.py::test_rca_lite_uses_structured_agent_runtime`

Expected: PASS.

## Task 6: ConclusionOutput Schema and Runtime

**Files:**
- Modify: `app/core/workflow/schemas.py`
- Modify: `app/core/workflow/nodes/conclusion_formatter.py`
- Test: `tests/unit/workflow/test_context_handoff.py`

- [ ] **Step 1: Write failing schema test**

Add a test validating:

```python
ConclusionOutput.model_validate({
    "title": "诊断报告",
    "diagnosis_overview": {"layer": "L3"},
    "evidence_chain": [],
    "root_cause": "节点无法访问 Docker Hub",
    "recommendations": ["配置镜像代理"],
    "limitations": [],
    "markdown_report": "## 诊断报告\n..."
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest -q tests/unit/workflow/test_structured_schemas.py::test_conclusion_output_schema_accepts_report_payload`

Expected: FAIL because `ConclusionOutput` does not exist.

- [ ] **Step 3: Add schema**

Add `ConclusionOutput` to `app/core/workflow/schemas.py` with fields from the test.

- [ ] **Step 4: Update conclusion LLM path**

In `_generate_with_llm()`, replace `ai_call.call_simple()` with `_call_structured_agent(..., ConclusionOutput, use_tools=False)`. Use `structured.markdown_report` as the returned report. If structured output is missing, return a concise failure report instead of parsing text.

- [ ] **Step 5: Run tests**

Run: `.venv/bin/python -m pytest -q tests/unit/workflow/test_context_handoff.py tests/unit/workflow/test_structured_schemas.py`

Expected: PASS.

## Task 7: Remove Node-Level Structured Extraction Duplication

**Files:**
- Modify: `app/core/workflow/nodes/layer_classifier.py`
- Modify: `app/core/workflow/nodes/evidence_collector.py`
- Test: `tests/unit/workflow/test_fast_paths.py`
- Test: `tests/unit/workflow/test_evidence_dynamic_stop.py`

- [ ] **Step 1: Replace local extraction helpers**

Replace `_structured_layer_from_response()` and `_structured_evidence_from_response()` internals with `StructuredAgentRuntime.extract_structured_response(...)`.

- [ ] **Step 2: Run targeted tests**

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_fast_paths.py::test_layer_agent_structured_output_skips_layer_extract_call \
  tests/unit/workflow/test_evidence_dynamic_stop.py::test_evidence_agent_structured_output_combines_plan_tools_and_summary
```

Expected: PASS.

## Task 8: Config Convergence

**Files:**
- Modify: `deploy/configmap/config.yaml`
- Modify: node config readers if needed.
- Test: existing workflow tests.

- [ ] **Step 1: Add unified config section**

Add:

```yaml
workflow:
  structured_runtime:
    enabled: true
    fallback_enabled: true
    nodes:
      layer: true
      evidence: true
      rca: true
      conclusion: true
```

Keep existing `layer.agent_structured_output`, `evidence.agent_structured_output`, `extract_fallback`, and `plan_precall_fallback` as compatibility aliases.

- [ ] **Step 2: Add config helper**

Add base helper methods:

```python
def _is_structured_runtime_enabled(self, default=True): ...
def _is_structured_runtime_fallback_enabled(self, default=True): ...
```

- [ ] **Step 3: Run tests**

Run: `.venv/bin/python -m pytest -q tests/unit/workflow/test_fast_paths.py tests/unit/workflow/test_evidence_dynamic_stop.py tests/unit/workflow/test_context_handoff.py`

Expected: PASS.

## Task 9: Full Regression

**Files:**
- All modified files.

- [ ] **Step 1: Compile modified modules**

Run:

```bash
python3 -m py_compile \
  app/core/aicall/client.py \
  app/core/workflow/structured_runtime.py \
  app/core/workflow/nodes/base.py \
  app/core/workflow/nodes/layer_classifier.py \
  app/core/workflow/nodes/evidence_collector.py \
  app/core/workflow/nodes/root_cause_analyzer.py \
  app/core/workflow/nodes/conclusion_formatter.py \
  app/core/workflow/schemas.py
```

Expected: no output.

- [ ] **Step 2: Run targeted regression**

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/unit/aicall/test_event_loop_safety.py \
  tests/unit/workflow/test_structured_runtime.py \
  tests/unit/workflow/test_structured_schemas.py \
  tests/unit/workflow/test_fast_paths.py \
  tests/unit/workflow/test_evidence_dynamic_stop.py \
  tests/unit/workflow/test_context_handoff.py \
  tests/unit/workflow/test_query_direct_mode.py
```

Expected: all pass.

## Self-Review

- Spec coverage: covers unified runtime, schema-only structured outputs, low coupling via one helper, RCA/conclusion convergence, fallback control, and tests.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: `StructuredAgentRuntime`, `StructuredAgentSpec`, `ConclusionOutput`, `_call_structured_agent`, and `response_schema` names are consistent across tasks.
