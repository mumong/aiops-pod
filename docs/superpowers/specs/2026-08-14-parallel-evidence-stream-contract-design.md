# Parallel Evidence Stream Contract Design

## Goal

Make live multi-anomaly tool results map to their authoritative anomaly group and, when available, exact Pod without depending on truncated text. Correct same-name concurrent call pairing, semantic failure rendering, and expanded result value while preserving every non-parallel workflow and existing diagnostic capability.

## Scope

This change is limited to the live `parallel_evidence` event path and its grouped Frontend board. It does not change MCP tools, evidence planning, diagnosis, Fact Ledger, node handoff contents, final reports, single-anomaly rendering, remediation, deployment, or context-budget behavior.

## Authoritative identity

The Layer node already builds `layer_handoff` through `LayerHandoff.model_validate(...)`. Its `issue_groups`/`abnormal_groups` contain authoritative `group_id` and `entities`. `ParallelEvidenceNode` creates one scoped handoff per group. The group collector will wrap only its live event queue and attach that scoped group identity to emitted events.

The Backend projects a small validated contract:

```json
{
  "contract_version": "aiops.parallel-evidence-stream.v1",
  "group_id": "g3",
  "entity": {
    "kind": "Pod",
    "namespace": "aiops-case-09",
    "name": "workload-..."
  },
  "dimension": "logging",
  "source_system": "elasticsearch"
}
```

`entity` is optional. It is emitted only when structured tool output or tool arguments identify an exact entity that belongs to the scoped group. A group-scoped tool without a unique Pod retains `group_id` but does not fabricate an entity.

## Event behavior

- `tool_start` and `tool_result` carry `tool_call_id` plus the validated evidence context.
- The Frontend pairs pending and returned calls by `group_id + tool_call_id`; legacy events fall back to the existing tool-name behavior.
- Group assignment uses `group_id` first, then exact structured entity, then the existing preview parser only as a backward-compatible fallback.
- `semantic_success=false` renders the parallel result as failed even if the transport-level status is `success`.
- For parallel results only, SSE includes the complete processed tool summary already held in the internal event plus artifact references. The 200-character preview remains a compact display field and never controls attribution.
- Expanded UI wording is changed from “完整原始结果” to “完整工具结果摘要”; archive references identify where raw/structured/summary artifacts live.

## Compatibility and safety

Non-parallel events keep the current bounded payload and behavior. Missing or malformed context falls back safely. Unknown group IDs are not guessed. Full raw tool blobs remain in Context Archive rather than being copied into SSE.

## Truncation audit disposition

This patch fixes only the four approved defects: preview-driven attribution, same-name call pairing, semantic-failure display, and 200-character expanded details. Other findings—multi-group conclusion input growth, prefix-only conclusion truncation, QUERY fallback truncation, and legacy 1600-character group summaries—are recorded but unchanged.

## Verification

Tests must prove validated group/entity projection, group-only results without fake entities, exact concurrent call pairing, truncated-preview independence, semantic failure display, full processed summary availability, legacy fallback compatibility, unchanged non-parallel projection, and successful Backend/Frontend regression suites and builds.
