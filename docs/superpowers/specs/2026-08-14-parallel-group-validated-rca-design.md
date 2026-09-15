# Parallel Group Validated RCA Design

## Goal

Improve only the multi-anomaly `parallel_evidence` path so every anomaly group uses the same Fact Ledger-backed RCA semantics as the existing single path, and so facts referenced by that validated RCA survive aggregation and appear first in the final report.

The single-anomaly path, tool contracts, Case definitions, graph threshold, deployment, remediation flow, and MCP implementations remain unchanged.

## Confirmed failure boundary

The collector already returns decisive canonical facts. For example, real archived tool data contains Kubernetes resource limits and Prometheus metric labels such as `reason=OOMKilled`. The current multi path loses them after collection:

```text
group-scoped EvidenceCollector
  -> aggregate_group_evidence projects each record to four fields
  -> GROUP_EVIDENCE_SUMMARY_PROMPT performs an independent mini-RCA
  -> conclusion LLM receives the narrowed projection
  -> entity table renders facts[:3] by insertion order
```

The existing single path instead sends canonical Fact Ledgers into `RootCauseAnalyzerNode` and validates all model fact references through `validate_rca_claims`. The defect is therefore in the parallel post-collection path, not a general inability of the tools to collect evidence.

## Approved approach: localized per-group formal RCA

Each group keeps its isolated collector and archive. Immediately after collection, the parallel worker runs one `RootCauseAnalyzerNode` against that group's scoped state and unchanged `evidence_analysis`. This reuses the existing RCA prompt, Fact Ledger extraction, fact-reference validation, downgrade behavior, and uncertainty semantics.

No global N-group RCA is added. A global RCA would rebuild a large shared context and reintroduce cross-entity contamination. The authoritative unit is one validated RCA result per anomaly group.

```text
layer
  -> parallel_evidence
       -> group g1: collector -> formal RCA -> GroupDiagnosisBundle
       -> group g2: collector -> formal RCA -> GroupDiagnosisBundle
       -> group gN: collector -> formal RCA -> GroupDiagnosisBundle
  -> deterministic conclusion fan-in
```

## Strong group handoff

The existing `group_results[]` envelope remains the public state contract. Each successful group adds these authoritative fields:

```json
{
  "rca_analysis": {"diagnostic_status": "diagnosed", "hypotheses": []},
  "diagnostic_status": "diagnosed",
  "entity_summaries": [
    {
      "namespace": "ns",
      "name": "pod",
      "root_cause": "validated hypothesis summary",
      "supporting_fact_ids": ["fact-..."],
      "contradicting_fact_ids": [],
      "confidence": 0.91,
      "claim_validation": {"valid": true}
    }
  ],
  "dimension_evidence_by_entity": {}
}
```

`evidence_analysis` and per-group archive references remain unchanged and retain the original collector output. The new handoff does not copy arbitrary raw blobs.

## Lossless canonical fact projection inside the multi path

`aggregate_group_evidence` will prefer canonical `fact_ledger.records` for every supported dimension, including Kubernetes. Each projected fact retains all canonical and future record fields by copying the record before adding a separate human-readable `display_value`. This preserves `attribute`, raw `value`, `unit`, `metadata`, timestamps, directness, confidence, strength, provenance, and any unknown extension fields.

Legacy structured output without a Fact Ledger continues to use the existing deterministic Kubernetes fallback. This is generic contract behavior; there are no Case IDs, fault names, metric names, or special tool branches.

Metric label rendering is generic. Compact labels that distinguish a series are appended to `display_value`; identity/noise labels may be omitted from presentation, but remain intact in `metadata`.

## Mapping validated RCA to entities

Formal RCA hypotheses are mapped by canonical `entity_id` to the exact scoped Pod. A multi-entity group gets one entity summary per scoped Pod:

- The matching validated hypothesis supplies root cause, supporting and contradicting fact IDs, unknowns, and confidence.
- A single-entity group may use the validated top-level RCA fields when the model did not emit a separate hypothesis.
- An entity without valid supporting facts remains `inconclusive` with `root_cause=证据不足`.
- Cross-entity or unknown fact IDs have already been removed or downgraded by `validate_rca_claims` and are never restored during mapping.

The old `GROUP_EVIDENCE_SUMMARY_PROMPT` mini-RCA is removed from this path so there is one root-cause authority per group.

## Deterministic fan-in and evidence ranking

The multi conclusion no longer asks another LLM to reinterpret group root causes. It emits a deterministic cluster overview from the validated group diagnoses, followed by the existing entity cards and folded raw tool sections.

Within each dimension, displayed facts are ordered by:

1. `supporting_fact_ids` in validated RCA order;
2. `contradicting_fact_ids` in validated RCA order;
3. remaining direct/high-confidence facts by strength, directness, and confidence;
4. remaining context facts.

All RCA-referenced facts are shown. Non-referenced context remains bounded for readability and the complete canonical records remain in `group_results` and the archive. There is no insertion-order `facts[:3]` authority.

## Failure handling

- Collector failure: preserve the current per-group error result; other groups finish.
- RCA LLM/schema failure: reuse the formal RCA node's `inconclusive` fallback.
- Missing Fact Ledger: formal RCA may analyze legacy evidence, but the entity summary cannot claim a diagnosed result without validated supporting fact IDs.
- Missing dimension: preserve the existing `empty`, `absent`, `not_applicable`, `weak`, or `error` status. No evidence is fabricated.
- One group failure never changes another group's facts or diagnosis.

## Compatibility and impact boundary

Modified production behavior is limited to:

- `app/core/workflow/nodes/parallel_evidence.py`
- `app/core/workflow/group_evidence.py`
- the multi-group functions in `app/core/workflow/nodes/conclusion_formatter.py`

No graph routing or configuration change is required. Existing live SSE group attribution changes in the same worktree must be preserved.

## Acceptance criteria

1. Every collected parallel group invokes the formal RCA node with its own scoped handoff and original Fact Ledger-bearing `evidence_analysis`.
2. The weak mini-RCA is not invoked.
3. Canonical fields and unknown extensions survive multi-group aggregation.
4. Kubernetes resource-limit records and metric reason labels are available to the report renderer.
5. Validated supporting facts appear before lifecycle/context facts regardless of collection order.
6. Unsupported or cross-entity diagnoses are downgraded to inconclusive.
7. A failure in one group does not prevent other groups from producing validated diagnoses.
8. Existing single-path tests and graph routing behavior remain unchanged.

