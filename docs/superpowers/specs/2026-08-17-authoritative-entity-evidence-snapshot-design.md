# Authoritative Entity Evidence Snapshot Design

## Context

The deployed `11.0.107` multi-anomaly path runs one evidence collector and one
formal RCA per issue group, then renders per-entity observability cards
deterministically. Live run `acc55839c41e4794` proved that collection can
produce useful Kubernetes, Prometheus, Elasticsearch, DeepFlow, and Tempo
responses, but the result still loses validated diagnoses during fan-in.

The immediate cause is duplicate fact projection:

1. `evidence_analysis.tool_data` is normalized into canonical Fact Ledgers for
   RCA and claim validation.
2. `thinking_events` is independently projected by `group_evidence.py` for the
   final report. Kubernetes observations without an embedded ledger receive
   newly derived `fact-k8s-*` IDs.
3. `ParallelEvidenceNode._attach_validated_diagnosis()` resolves RCA supporting
   IDs against the second projection. Canonical IDs from the first projection
   do not resolve, so a validated diagnosis is replaced by an inconclusive
   fallback.

The same run exposed three adjacent failures: the legacy Kubernetes adapter
does not retain waiting/event messages, a multi-entity status group may collect
lifecycle evidence for only one Pod, and Tempo can report successful lookups
without producing span facts.

## Goals

- Use one immutable, per-entity fact registry for RCA input, claim validation,
  handoff, and final rendering.
- Preserve source-backed high-value fields across compaction without defining
  fault-case-specific schemas.
- Diagnose each Pod independently even when the layer classifier groups Pods
  by the same coarse status.
- Rank evidence by generic diagnostic role and truth semantics rather than by
  tool order or Case ID.
- Represent Tempo coverage and log/flow/span correlation truthfully.
- Verify the change with archived replay, unit tests, a real image deployment,
  and fixed-protocol N=1/3/5/10 live runs.

## Non-goals

- Do not encode rules for c01-c11 or known workload names.
- Do not infer facts not returned by a source system.
- Do not replace the current workflow graph or introduce a new database.
- Do not claim exact cross-dimensional correlation when trace IDs differ.
- Do not mutate code between runs in one live-test series.

## Architecture

### EntityEvidenceSnapshot

After a scoped collector completes, its authoritative tool data is normalized
once into an `EntityEvidenceSnapshot`:

```text
EntityEvidenceSnapshot
├── entities: canonical entity identity index
├── fact_ledgers: exact normalized ledgers
├── fact_index: fact_id -> complete FactRecord
├── facts_by_entity_and_dimension
├── coverage_by_entity_and_dimension
├── limitations
└── archive references
```

The snapshot is a projection over existing Fact Ledger records, not a second
fact format. Unknown canonical record extensions are copied intact. Raw and
summary references remain available for drill-down.

The data flow becomes:

```text
tool raw/structured result
        |
        v
canonical/legacy Fact Ledger normalization (once)
        |
        v
EntityEvidenceSnapshot
   |          |             |
   v          v             v
RCA input  claim check  final entity cards
```

`thinking_events` remains the audit and progressive-stream source, but it can
no longer mint diagnostic Fact IDs or override snapshot facts.

### Generic Kubernetes source facts

The legacy Kubernetes adapter will emit atomic, source-backed records for:

- Pod phase, conditions, and current status;
- container waiting/terminated reason, message, and exit code;
- restart count and resource requests/limits;
- Event type, reason, message, source, and observed time;
- bounded source fragments with a source path, content hash, and archive
  reference when a structured field has no first-class adapter yet.

The adapter classifies generic diagnostic roles in metadata:

- `causal_candidate`: a direct warning/error/waiting/event message;
- `symptom`: state, exit code, restart count, or response outcome;
- `contradicting`: a direct observation that weakens a hypothesis;
- `context`: topology, configuration, or successful background activity;
- `negative_observation`: a categorical/binary series whose observed value is
  zero.

These roles describe source semantics and do not name fault cases.

### Atomic Pod lanes

Layer issue groups remain useful for presentation, but `parallel_evidence`
normalizes every Pod into an atomic diagnostic lane before collection. Each
lane gets its own collector budget, snapshot, RCA, and archive. Parent group
identity is retained for deterministic fan-in.

This prevents one Pod in a coarse `ContainerCreating` or `CrashLoopBackOff`
group from consuming the lifecycle/tool budget of another Pod.

### Per-entity RCA validation

RCA validation resolves only against the snapshot fact index. A diagnosed
entity must retain at least one valid, in-scope supporting fact and at least one
source-backed causal candidate or direct lifecycle cause. Missing evidence for
one entity does not erase a valid hypothesis for another entity.

If structured RCA output is invalid, the report still renders the snapshot. A
direct, strong lifecycle blocker can be shown as an observed blocking cause
with its existing Fact ID; free-form LLM text is never converted into a fact.

### Evidence selection and display

The report orders facts as follows:

1. RCA supporting facts;
2. RCA contradicting facts;
3. direct causal candidates;
4. symptoms;
5. context.

Coverage/status markers, table headers, and summarizer states are not facts.
Zero-valued categorical series are rendered only as negative/exclusion
observations. Restart counts are persistence evidence unless an RCA explicitly
uses them with a causal fact. Complete metric identity labels and query purpose
remain available in the expandable detail.

### Tempo and correlation truthfulness

In `mcpstander`, a successful HTTP lookup is not evidence coverage. Tempo is
`present` only when at least one valid span is parsed. Parsed spans become
canonical tracing FactRecords. A successful query with no spans is `empty`.

Logs, flows, and spans are marked `correlated` only for an exact normalized
trace ID match. Same-Pod/path/status observations without an exact match are
reported as related context.

## Error handling

- Invalid canonical records are excluded with an explicit limitation and
  remain available through archive references.
- A snapshot with missing dimensions stays valid and records coverage honestly.
- A failed entity lane does not cancel sibling lanes.
- RCA schema failure does not remove or rewrite snapshot facts.
- Fact-ID collisions, out-of-scope references, or non-causal-only diagnoses
  downgrade only the affected entity.

## Testing and completion evidence

### Archived replay

Fixtures derived from `acc55839c41e4794` must prove:

- c04 waiting message survives tool data -> snapshot -> RCA -> report;
- c05 network-definition event survives the same path;
- c03 and c05 have independent lifecycle coverage;
- c09 and c10 retain valid diagnoses when supporting Fact IDs resolve;
- the same Fact ID appears in RCA validation and final output;
- zero-valued reason series, table headers, and summarizer states cannot become
  positive root evidence;
- Tempo `present` requires span facts.

### Live deployment and fixed test protocol

After focused and full unit suites pass, increment the image version and run:

```bash
make delete
make build
make push
make deploy
```

Verify backend, mcpstander, and frontend connectivity. Then, without changing
code during the series, run a healthy baseline, N=1 OOM, N=1 randomly selected
non-OOM case, and N=3/N=5/N=10 anomaly sets. Record wall time per run, tool
counts, entity/dimension coverage, diagnosed/inconclusive status, invalid Fact
IDs, and a manual value review of the final report.

## Acceptance criteria

- RCA, validation, and final rendering consume the same fact registry.
- No validated entity diagnosis is discarded because of a projection-only ID
  mismatch.
- Every abnormal Pod receives an independent diagnostic lane and lifecycle
  coverage attempt.
- High-value source facts survive compaction generically and retain source
  references.
- Reports distinguish causal, symptom, negative, and contextual evidence.
- Tempo and trace correlation labels match the facts actually preserved.
- All automated tests pass, the new image deploys successfully, and the full
  fixed live-test series completes with an auditable result report.
