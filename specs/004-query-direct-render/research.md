# Research: Query Direct Render

## Decision: Query direct conclusion renders locally from `query_result`

**Rationale**: The production failure had a valid `query_result` but the second conclusion LLM returned empty content. Local rendering removes that failure mode and restores deterministic output.

**Alternatives considered**:
- Keep structured conclusion LLM: rejected because it already caused "LLM 未返回有效内容" and adds latency.
- Retry conclusion LLM: rejected because it adds more latency and still depends on model formatting.

## Decision: Query direct may parse JSON text from the first LLM/tool loop

**Rationale**: The user requested the previous architecture: one LLM/tool call with JSON output in the prompt, not Pydantic structured extraction. JSON text parsing keeps the first loop flexible while avoiding `layer_extract` latency.

**Alternatives considered**:
- Pydantic `call_structured` extraction: rejected for `/query` direct because it created the 131 second layer_extract delay in the observed run.
- Pure tool-event extraction only: kept as fallback, but JSON text remains useful when the LLM already formats the query result correctly.

## Decision: Prometheus tool-event fallback remains required

**Rationale**: Some providers emit empty final text after tool calls. Tool events are archived and evidence-grounded, so the system can still build a reliable query result.

**Alternatives considered**:
- Fail when JSON text is missing: rejected because the observed run had useful tool data.

## Decision: `/ask` stays on existing diagnosis path

**Rationale**: Diagnosis and remediation plans need richer structured schemas and safety checks. The user explicitly scoped this fix to `/query`.

**Alternatives considered**:
- Reuse query JSON extraction in `/ask`: rejected as scope creep and possible regression.
