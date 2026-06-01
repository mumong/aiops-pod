# Feature Specification: Ask Layer Structured Fallback

**Feature Branch**: `006-ask-layer-structured-fallback`

**Created**: 2026-06-01

**Status**: Draft

**Input**: User description: "Analyze and fix why `/ask` now fails at layer with `layer 未能生成 Pydantic LayerOutput`. Keep the change scoped to `/ask` layer stability and do not affect `/query` or the final remediation approval semantics. Use Speckit and verify with real runs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Clear LLM Unavailable Failure (Priority: P1)

An operator calls `/ask` while the configured LLM endpoint is unreachable. The workflow must fail fast with a clear LLM connectivity error instead of rendering an empty layer result and then reporting an opaque Pydantic `LayerOutput` failure.

**Why this priority**: The current production failure is caused by `LLM_API_BASE` refusing connections, but the user-facing error points at Pydantic extraction and hides the operational cause.

**Independent Test**: Simulate a layer agent response that contains only `Agent 执行异常: Connection error.` and verify the node raises an explicit LLM unavailable error without a second layer extraction attempt.

**Acceptance Scenarios**:

1. **Given** the layer agent returns a connection-error synthetic result and no successful tool evidence, **When** `/ask` layer executes, **Then** it raises a clear LLM unavailable error.
2. **Given** the LLM endpoint is restored, **When** `/ask` layer executes, **Then** normal structured layer extraction remains available.

---

### User Story 2 - Structured Fallback When Native Pydantic Is Unsupported (Priority: P1)

An operator calls `/ask` against a local OpenAI-compatible gateway that can answer plain JSON prompts but does not support native structured output. The layer extraction should fall back to prompt JSON plus Pydantic validation.

**Why this priority**: Native structured output is a fragile integration point on local gateways; `/ask` should not fail solely because native structured mode is unsupported when normal LLM calls still work.

**Independent Test**: Simulate native structured failure with text fallback enabled and verify layer receives a valid `LayerOutput`.

**Acceptance Scenarios**:

1. **Given** native structured output returns no object but text JSON fallback returns valid layer JSON, **When** layer extraction runs, **Then** the workflow continues with validated `LayerOutput`.
2. **Given** fallback JSON is invalid, **When** layer extraction runs, **Then** the workflow does not invent a layer and reports a clear extraction failure.

---

### User Story 3 - Query Path Unchanged (Priority: P1)

An operator uses `/query`. The `/query` direct path must keep its current direct JSON/tool-result rendering and must not reintroduce slow Pydantic extraction.

**Why this priority**: The user explicitly separated `/query` performance problems from `/ask` diagnosis, and previous fixes restored query direct rendering.

**Independent Test**: Existing query direct tests continue to prove that query results are rendered without extra structured calls when a usable direct result or Prometheus tool result exists.

**Acceptance Scenarios**:

1. **Given** `/query` has a usable direct JSON result, **When** layer executes, **Then** it returns the query result without calling layer_extract.
2. **Given** `/query` has real Prometheus tool results, **When** layer executes, **Then** it builds the query result from those events as before.

### Edge Cases

- LLM host is reachable but configured port is closed.
- LLM agent returns a synthetic exception string instead of raising.
- Native structured output is unsupported, but normal text completion works.
- Native structured output and text fallback both fail.
- Stage 1 has successful tool evidence but the extraction LLM fails.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `/ask` layer MUST detect synthetic LLM connection failure text with no successful tool evidence and fail with a clear LLM-unavailable message.
- **FR-002**: `/ask` layer MUST NOT present `layer=None` or a zero-confidence successful-looking layer panel when the LLM endpoint is unavailable.
- **FR-003**: Layer structured extraction MUST request text JSON fallback when native structured output is unavailable.
- **FR-004**: The fallback result MUST still be validated by the existing `LayerOutput` schema before use.
- **FR-005**: The system MUST NOT synthesize a high-confidence diagnosis when both native and fallback structured extraction fail.
- **FR-006**: The change MUST NOT alter `/query` direct rendering or query direct performance gates.
- **FR-007**: The change MUST NOT alter remediation approval/rejection semantics.
- **FR-008**: Real validation MUST include deployed `/ask` behavior and backend logs; if the external LLM endpoint remains unavailable, validation must report that as an operational blocker rather than claim workflow success.

### Key Entities *(include if feature involves data)*

- **Layer Extraction Attempt**: The no-tool structured finalization step that converts collected layer text/tool evidence into a `LayerOutput`.
- **LLM Unavailable Signal**: A synthetic agent failure string or connection-refused exception proving the configured LLM endpoint cannot answer.
- **Validated LayerOutput**: A Pydantic-validated layer classification used by downstream evidence, RCA, and conclusion nodes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Focused unit tests prove that layer extraction passes `allow_text_fallback=True`.
- **SC-002**: Focused unit tests prove that connection-error synthetic results fail with a clear LLM unavailable error and do not perform duplicate extraction attempts.
- **SC-003**: Existing `/query` direct unit tests still pass.
- **SC-004**: Real deployed `/ask` test either reaches layer successfully when the LLM endpoint is healthy or reports the exact unreachable LLM endpoint when it is not.

## Assumptions

- `/ask` diagnosis fundamentally requires a working LLM endpoint for tool planning and interpretation.
- The code can improve error handling and native-structured fallback, but cannot diagnose the cluster when every LLM call is refused.
- The current deployed Secret value `LLM_API_BASE=http://10.2.0.54:4000/v1` is an operational dependency outside the application image.
