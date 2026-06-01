# Feature Specification: Query Direct Render

**Feature Branch**: `004-query-direct-render`

**Created**: 2026-06-01

**Status**: Draft

**Input**: User description: "Use Speckit to restore the stable `/query` path: only modify query-chain logic, do not affect existing `/ask`; `/query` should use the previous single LLM tool call plus JSON text structure extraction, then deterministic conclusion rendering. Do not use Pydantic for query structure extraction."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fast Metric Query Result (Priority: P1)

An operator calls `/query` to ask for node CPU and memory usage and receives a readable Markdown table based on the real Prometheus results without a second summary LLM call.

**Why this priority**: This is the broken production flow reported by the user. It directly affects the usability and latency of metric queries.

**Independent Test**: Run a `/query` request for CPU and memory usage and verify the final report contains the structured metric table, not a raw-data failure fallback.

**Acceptance Scenarios**:

1. **Given** Prometheus tool calls return successful CPU and memory vectors, **When** the `/query` direct workflow reaches conclusion, **Then** the final report is rendered locally from `query_result` and contains node rows and metric columns.
2. **Given** the query result already exists in workflow state, **When** conclusion executes, **Then** no conclusion LLM call is required for the `/query` response.

---

### User Story 2 - Preserve Ask Diagnosis Flow (Priority: P1)

An operator calls `/ask` for diagnosis or remediation planning and receives the same diagnosis behavior as before this query-only repair.

**Why this priority**: The user explicitly limited the change scope to `/query`; `/ask` must not lose Pydantic diagnosis schemas, remediation plan handling, or safety review behavior.

**Independent Test**: Execute existing unit tests that cover `/ask` diagnosis conclusion and remediation handling; verify changed code paths are gated by query direct mode.

**Acceptance Scenarios**:

1. **Given** a non-QUERY diagnosis state, **When** conclusion executes, **Then** it still uses the existing diagnosis conclusion path.
2. **Given** the workflow is not in query direct mode, **When** layer classification runs, **Then** it does not use the query-only JSON extraction shortcut.

---

### User Story 3 - Avoid Query Planning Noise (Priority: P2)

An operator sees a concise query answer rather than TodoWrite planning output, runbook excerpts, or unrelated metadata metrics.

**Why this priority**: Planning/tool noise caused confusing output and increased latency. Fixing the main result is P1; reducing noise is next.

**Independent Test**: Simulate query direct tool events containing TodoWrite and metadata queries; verify final query result excludes TodoWrite and does not treat `node_uname_info` as a metric column.

**Acceptance Scenarios**:

1. **Given** tool events include TodoWrite, **When** query result is built, **Then** TodoWrite is not included in query rows or final Markdown.
2. **Given** tool events include `node_uname_info`, **When** query result is built for CPU/memory, **Then** node metadata may assist labels but must not create a `metric_3` usage column.

### Edge Cases

- If the LLM emits no JSON but Prometheus tool events are available, the system must still build `query_result` from real tool events.
- If no usable query rows are available, the final `/query` response must be a clear "未获取到" result, not a raw transcript dump.
- If a query direct request includes remediation-related runtime configuration, query rendering must ignore remediation plan output and remain read-only.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `/query` direct MUST produce the final user-facing answer from a structured `query_result` via deterministic local rendering.
- **FR-002**: `/query` direct MUST NOT call the conclusion LLM when a valid `query_result` is present.
- **FR-003**: `/query` direct MUST support JSON text extraction from the first LLM/tool collection response without requiring Pydantic `call_structured`.
- **FR-004**: `/query` direct MUST retain a fallback that builds `query_result` from successful Prometheus tool events when the LLM JSON text is missing or unusable.
- **FR-005**: Query-only JSON extraction and rendering MUST be gated by `query_mode=direct` and `layer=QUERY`.
- **FR-006**: `/ask` diagnosis, remediation approval, and diagnosis conclusion paths MUST remain functionally unchanged.
- **FR-007**: Query result construction MUST exclude TodoWrite and other planning tools from query data.
- **FR-008**: Query result construction MUST treat node metadata queries such as `node_uname_info` as metadata, not as a usage metric column.
- **FR-009**: If query data is unavailable, the response MUST render a concise missing-data report using structured missing reasons instead of exposing raw tool transcripts.

### Key Entities *(include if feature involves data)*

- **QueryResult**: User-facing structured query answer containing target, collection summary, columns, rows, notes, missing reasons, and sources.
- **Query Tool Event**: A real tool observation from the first LLM/tool collection loop, including tool name, arguments, status, semantic success, and result payload.
- **Query Mode**: Workflow runtime mode that distinguishes `/query` direct from `/ask` diagnosis.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A CPU/memory `/query` with successful Prometheus results returns a Markdown table and never returns "报告生成失败：LLM 未返回有效内容".
- **SC-002**: The same CPU/memory `/query` path uses at most one LLM/tool collection cycle plus local rendering when Prometheus results are sufficient.
- **SC-003**: Focused unit tests prove that query conclusion does not call `call_structured` or `call_simple` when `query_result` exists.
- **SC-004**: Focused unit tests prove that non-query diagnosis conclusion behavior is still routed through the existing diagnosis path.
- **SC-005**: Real deployment validation shows `/query` completes substantially faster than the observed 2.9 minute regression and includes performance statistics in the final streamed output.

## Assumptions

- Existing Prometheus MCP tools remain the source of truth for node-level CPU and memory data.
- The first LLM/tool collection loop may still call multiple tools; the repair only changes query result extraction, filtering, and rendering.
- Existing `/ask` remediation safety behavior is out of scope except where tests verify it remains untouched.
