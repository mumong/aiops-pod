# Authoritative Evidence B2 Design

## 1. Status and objective

Status: approved design direction, pending implementation plan and code changes.

The objective is to make single- and multi-entity diagnosis stable when the
LLM is small, inconsistent, or partially wrong. The implementation must retain
real high-value Kubernetes, metrics, logging, and tracing evidence through
collection, compaction, RCA, claim validation, archival, and final rendering.

Wall time is measured and optimized, but it is not a correctness acceptance
gate. The implementation must prefer an auditable correct result over a fast
unsupported result. Efficiency work must reduce duplicated model/tool work and
orchestration wait; it may not remove required evidence or weaken validation.

The system must not encode workload names, Case IDs, expected root causes,
metric names, log strings, Kubernetes reasons, or scenario-specific fixes in
production policy. Regression fixtures may contain concrete examples, but the
implemented behavior must be driven only by generic contracts and source
semantics.

## 2. Evidence from the frozen validation series

The frozen `11.0.108`/`7.0.27` series establishes these facts:

- Measurement integrity and final Fact-ID entity isolation pass at N=1, N=3,
  N=5, and N=10.
- The parallel path renders valid canonical Fact IDs, but a rendered ID does
  not prove persisted formal RCA or claim authorization.
- `EntityEvidenceSnapshot` is created inside each lane and passed in memory,
  but the top-level executor has no `parallel_evidence` snapshot projection;
  the archived base snapshot is therefore `{}`.
- Each lane executes `RootCauseAnalyzerNode`, but the node archives only its
  input. Formal RCA output and claim-validation output are not persisted.
- A model-generated hypothesis can mutate an entity UID. The current gate
  safely rejects it, but the lane becomes inconclusive even when all referenced
  facts are correctly bound.
- A direct, strong Kubernetes event can retain legacy metadata role `context`,
  causing a decisive fact to be under-ranked even though it reaches RCA.
- At N=10, decisive facts can reach RCA input while the model still returns an
  inconclusive or internally contradictory result.
- The N=10 wall time is 792.139 seconds; the evidence node alone is 659.709
  seconds. The current lane worker holds one of three worker slots while it
  performs both evidence collection and formal RCA.

These are contract, orchestration, persistence, and scheduling defects. They
are not solved by adding more prompt text or by enumerating known anomalies.

## 3. Considered approaches

### 3.1 Archive-only patch

Add executor serialization for existing `group_results` and write RCA output
files. This is the smallest change, but it only makes failures observable. It
does not prevent malformed entity IDs, model bypass, evidence-role loss, or
load-dependent inconclusive results.

Decision: rejected as incomplete.

### 3.2 B2 authoritative evidence and claim pipeline

Keep the existing Layer, Evidence, RCA, Conclusion, Fact Ledger, and parallel
lane architecture. Make identity, evidence selection, persistence, claim
validation, final projection, and retry policy deterministic. Treat the LLM as
an untrusted candidate generator inside a constrained lane.

Decision: selected. This is the smallest design that addresses all observed
causal locations without replacing the application architecture.

### 3.3 Deterministic anomaly-specific RCA engine

Encode root-cause rules for Kubernetes reasons, resource events, logs, metrics,
and traces. This can be stable for known fixtures but would require an
ever-growing scenario registry and violate the no-special-case requirement.

Decision: rejected.

## 4. Non-negotiable invariants

### 4.1 Identity authority

- Namespace, name, kind, and UID come from source-backed Fact Ledgers and the
  scoped lane envelope, never from free-form LLM text.
- Parallel execution has exactly one authoritative Pod entity per lane.
- The LLM may describe a hypothesis but does not own or create its `entity_id`.
- Every referenced Fact ID must resolve to the same authoritative lane or an
  explicitly typed topology endpoint reachable from that lane.
- Ambiguous, unknown, foreign-lane, or colliding Fact IDs fail closed.
- No namespace/name/UID association may be guessed from text similarity.

### 4.2 Evidence authority

- `EntityEvidenceSnapshot` is built once from normalized Fact Ledgers.
- RCA input, claim validation, and deterministic rendering consume that same
  snapshot. They may select a bounded view but may not regenerate facts.
- Canonical facts are immutable after snapshot construction.
- Compaction removes only whole records. It never truncates a Fact ID, entity
  identity, source reference, label set required for identity, or numeric
  value into a semantically different object.
- Compaction records exactly which facts were selected and omitted, with a
  machine-readable reason.

### 4.3 Claim authority

- `diagnostic_status=diagnosed`, root cause, confidence, causal chain, and final
  supporting IDs are published only from a validated formal RCA result.
- An inconclusive or invalid formal RCA cannot be converted into a confident
  diagnosis by the conclusion LLM.
- Claim validation is fail-closed and persisted before conclusion rendering.
- The final report can display unselected context facts, but they must be
  labelled context and cannot silently become formal support.

### 4.4 No special-case policy

Production selection and retry logic may use only:

- canonical entity scope;
- dimension and fact type;
- source system and directness;
- confidence and strength;
- generic source severity and structured status fields;
- evidence role;
- timestamp, labels, units, and typed topology endpoints;
- validation outcome and missing/ambiguous references.

Production policy must not branch on Case ID, namespace, workload name,
specific expected root cause, specific metric name, or literal fixture output.

### 4.5 Agent and deterministic-code responsibility boundary

The LLM Agent is used only for work that benefits from semantic judgment:

- propose one or more causal hypotheses from an authoritative bounded Fact
  view;
- explain a causal chain using cited canonical Fact IDs;
- identify genuine unknowns and decide whether an additional scoped query is
  semantically useful;
- summarize limitations in human-readable language;
- propose remediation ideas after diagnosis, without executing them.

The LLM Agent is not trusted for work that requires exactness or repeatability:

- discovering or copying namespace/name/UID identity;
- binding a tool result or Fact to an entity;
- counting, deduplicating, ranking, truncating, or preserving facts;
- deciding whether four-dimensional minimum collection is complete;
- constructing PromQL/DSL scope outside validated tool contracts;
- serializing handoffs or archive artifacts;
- validating Fact IDs, topology endpoints, or claim scope;
- deciding final diagnostic status or publishable confidence;
- assembling factual tables or calculating coverage and continuity.

Those exact operations belong to deterministic code. The Agent may request an
operation, but code validates scope, executes it, normalizes the response, and
decides whether the result can enter the authoritative snapshot.

The baseline collector deterministically schedules the minimum source checks
needed for Kubernetes, metrics, logging, tracing, and topology according to
entity runtime state. The Agent may add bounded, scoped follow-up queries, but
it cannot cancel mandatory checks or relabel query failure as source absence.

## 5. Authoritative data contracts

### 5.1 EntityEvidenceSnapshot

The existing snapshot remains the evidence authority and retains:

```text
contract_version
entities[]
fact_ledgers[]
fact_index{fact_id -> complete canonical record}
dimension_evidence_by_entity{entity -> dimension -> projection}
limitations[]
archive_refs[]
```

It gains a deterministic selection manifest:

```text
selection_manifest:
  eligible_support_fact_ids[]
  required_context_fact_ids[]
  rca_input_fact_ids[]
  omitted_fact_ids[]
  omission_reasons{fact_id -> reason}
```

The manifest is derived from generic quality ordering and budget accounting.
It is not generated by the LLM.

### 5.2 LaneDiagnosisArtifact

Each lane persists one reloadable diagnosis envelope:

```text
contract_version
group_id
parent_group_id
presentation_index
authoritative_entities[]
snapshot_ref
snapshot_sha256
rca_input_ref
rca_attempts[]:
  attempt
  trigger
  model_output_ref
  validated_output_ref
  validation_status
selected_rca_ref
claim_validation_ref
final_projection_ref
diagnostic_status
```

Large evidence remains in the group archive. The envelope stores immutable
references and hashes so the complete chain can be reloaded without copying
raw tool output into WorkflowState.

### 5.3 Parallel handoff

`WorkflowState.group_results` remains the strong in-memory handoff. The
top-level `parallel_evidence.output.json` persists:

- contract version;
- ordered group index;
- complete lane result or reloadable lane artifact reference;
- exact entity identities;
- fact/RCA/final counts;
- completeness and diagnostic status;
- hashes for every referenced authoritative artifact.

The executor lifecycle snapshot may carry a compact projection for SSE, but
the archived node output must be reloadable and must not be `{}`.

## 6. Deterministic evidence selection

### 6.1 Generic role normalization

An explicit legacy role is advisory, not absolute. The canonical classifier
re-evaluates it from source semantics.

A fact is an eligible causal candidate when it is direct, source-backed,
strong enough for claim support, and its generic structure represents an
error/warning event, failing condition, lifecycle transition, termination,
waiting state, or structured failure message. This classification does not
recognize application-specific strings.

Configuration and measurement facts are retained as required context when
they are direct and strong, even when they are not independently causal.
Coverage-only, related-context, weak, or low-confidence records cannot support
a diagnosed claim.

### 6.2 Bounded diversity

Before global fill, RCA compaction preserves for each authoritative entity:

1. every eligible causal candidate that fits the hard contract budget;
2. at least one strongest direct record per available dimension;
3. required configuration/context records;
4. contradicting or negative observations;
5. remaining records by deterministic quality order.

If all mandatory records cannot fit, RCA must return a typed budget failure;
it must not silently claim that omitted data was absent.

### 6.3 Empty-state vocabulary

Every dimension uses one of these distinct states:

- `present`: canonical facts are retained;
- `unselected`: the source has data, but no record was selected for the current
  bounded RCA view;
- `not_applicable`: the entity state makes the runtime dimension inapplicable;
- `absent`: a valid source query proved no matching data;
- `error`: the source query or parser failed;
- `unknown`: the dimension was not reliably evaluated.

The final report must not translate `unselected` or `error` into `absent`.

## 7. Formal RCA with a small LLM

### 7.1 Model responsibility

The model receives:

- one authoritative lane identity;
- a compact canonical Fact Ledger view;
- the selection manifest;
- allowed Fact IDs;
- explicit output schema.

The model returns candidate summary, causal chain, confidence rationale,
supporting Fact IDs, contradicting Fact IDs, and unknowns. It does not choose
the lane entity identity.

### 7.2 Deterministic entity envelope

For a single-entity lane, the orchestrator injects the exact canonical entity
into every candidate before claim validation. A model-provided entity field is
retained only as diagnostic metadata and cannot override the lane envelope.

For a genuinely multi-entity non-parallel context, current strict resolution
remains: explicit exact identity or unique resolution from referenced facts;
otherwise fail closed.

This is not inferred Pod association: the lane was created from the scoped
source entity before the model call, and every supporting Fact ID is validated
against the same canonical identity.

### 7.3 One bounded repair attempt

A second RCA attempt is allowed only when all conditions are generic and
machine-verifiable:

- the first output is invalid or inconclusive;
- the snapshot contains at least one eligible support fact;
- the first failure is an output/claim defect rather than missing source data;
- the lane has remaining time budget.

The repair input contains the exact lane identity, eligible support facts,
required context, the first validation reasons, and the same schema. It does
not run tools or broaden scope. There is at most one repair attempt.

If the repair still fails, the lane remains inconclusive. Both attempts and
both validations are archived.

## 8. Persistence and reload sequence

For every lane, processing order is:

```text
tool observations
  -> normalized Fact Ledgers
  -> EntityEvidenceSnapshot
  -> persist snapshot + hash
  -> deterministic RCA selection manifest
  -> persist full RCA input + hash
  -> model candidate
  -> inject authoritative lane identity
  -> validate claims
  -> optional one bounded repair attempt
  -> persist model output, validated RCA, and claim validation
  -> build deterministic entity summary
  -> persist final projection
  -> return LaneDiagnosisArtifact in group_results
```

Conclusion receives only validated lane projections plus immutable snapshot
references. It does not recalculate root causes.

## 9. Final rendering

The authoritative entity card is deterministic:

- identity and status from the lane envelope;
- root cause, confidence, causal chain, supporting and contradicting IDs from
  the selected validated RCA;
- four-dimensional facts from the snapshot;
- limitations and empty-state vocabulary from source/selection metadata;
- artifact references and hashes from the lane diagnosis envelope.

Optional LLM narrative is non-authoritative and may only paraphrase the
validated RCA. It cannot change diagnostic status, confidence, entity,
supporting IDs, or facts. If formal RCA is inconclusive, the authoritative
report remains inconclusive regardless of narrative text.

The legacy N=1 path is brought under the same claim gate. It may keep its
existing node topology, but it cannot publish a diagnosis that contradicts an
inconclusive formal RCA.

## 10. Scheduling and efficiency

Correctness is implemented and verified before concurrency tuning. Latency is
an optimization metric, not a release gate.

The current parallel worker holds a collection slot during RCA. The revised
orchestrator separates bounded stages:

- collection executor: existing configured collection concurrency;
- RCA executor: separately bounded, tool-free formal RCA calls;
- conclusion: deterministic fan-in.

As soon as a lane snapshot is persisted, its RCA can enter the RCA executor
and the collection slot is released for another lane. Both limits are
configuration-driven, have hard maximums, and never change evidence or claim
rules. No Case-dependent scheduling is allowed.

Every lane records queue wait, collection time, RCA attempt time, validation
time, and archive time. The top-level report records critical paths rather
than only cumulative tool time.

Further optimization must be based on measured stage timings. Acceptance
criteria, evidence dimensions, Fact budgets, and claim gates may not be
weakened to improve wall time. Scheduler refactoring is performed only when a
measured critical path justifies its added complexity; the first repair may
retain the current scheduler if correctness is achieved without it.

## 11. Failure behavior

- Snapshot persistence failure: lane is inconclusive; no RCA is published.
- Snapshot hash/reload mismatch: lane is inconclusive and marked integrity
  error.
- Required mandatory facts exceed budget: typed budget error, no silent drop.
- Model output parse failure: optional bounded repair attempt.
- Unknown/cross-lane/colliding Fact ID: fail closed; optional bounded repair.
- Claim validation failure after repair: inconclusive with exact reasons.
- Archive failure after validated RCA: no final diagnosis, because the chain
  is not auditable.
- Dimension query failure: `error`, never `absent`.
- Conclusion narrative failure: deterministic entity cards remain available.

## 12. Code boundaries

Expected focused modifications:

- `app/core/workflow/entity_evidence_snapshot.py`
  - selection manifest and reload validation.
- `app/core/workflow/fact_contract.py`
  - generic role normalization, mandatory Fact selection, and authoritative
    single-lane entity injection/validation metadata.
- `app/core/workflow/nodes/root_cause_analyzer.py`
  - persist validated output, bounded repair attempt, and claim artifact.
- `app/core/workflow/nodes/parallel_evidence.py`
  - lane artifact creation and separated bounded stages.
- `app/core/workflow/executor.py`
  - non-empty parallel snapshot/archive projection and group artifact index.
- `app/core/workflow/nodes/conclusion_formatter.py`
  - formal-RCA fail-closed authority for both legacy and parallel paths.
- `app/core/context/archive.py` or a focused workflow artifact helper
  - atomic JSON artifact writes, hashes, and reload checks.
- `app/core/workflow/state.py`
  - typed authoritative group artifact fields.

No MCP query schema or Case manifest change is planned unless a failing test
proves a source-contract defect outside these boundaries.

## 13. Test strategy

All production changes use red-green-refactor.

### 13.1 Unit gates

- Snapshot round-trip retains every canonical fact, unknown extension, label,
  evidence reference, role, limitation, and selection decision.
- Parallel executor archive is reloadable and never `{}` when lanes exist.
- Group archives contain snapshot, RCA input, every model attempt, validated
  RCA, claim validation, and final projection.
- A deliberately mutated model entity cannot change the authoritative lane;
  foreign Fact IDs still fail closed.
- Strong direct generic warning/failure events cannot remain weak context due
  solely to legacy metadata.
- Mandatory causal/context facts survive bounded compaction or produce a typed
  budget error.
- Query `unselected`, `not_applicable`, `absent`, and `error` render distinctly.
- First invalid RCA plus eligible facts triggers exactly one constrained repair;
  success publishes validated support, second failure remains inconclusive.
- Legacy and parallel conclusion paths cannot override invalid formal RCA.
- Scheduling tests prove collection slots are released before RCA finishes and
  both stage limits are enforced.

### 13.2 Offline retained-artifact replay

Replay the frozen ledgers and RCA inputs through the new deterministic layers.
Concrete incidents are regression data only; production logic remains generic.
Verify exact identity, decisive-fact retention, archive reload, claim outcome,
and deterministic display.

### 13.3 Live closure

Under one new frozen image version:

1. build, push, deploy, and verify fresh image digest/Pod UID;
2. healthy baseline with zero Case namespaces;
3. N=1 OOM and N=1 non-OOM;
4. fixed N=3, N=5, and N=10 sets;
5. one SSE request per run, unchanged prompt contract;
6. independent validation of every lane and every artifact chain;
7. N=10 wall time and per-stage critical paths are recorded and compared
   without imposing a correctness timeout gate;
8. zero invalid/cross-lane final support;
9. every diagnosed lane has reloadable snapshot -> RCA -> claim -> final Fact
   continuity;
10. independent reviewer `ACCEPT` before declaring closure.

## 14. Acceptance definition

B2 is complete only if:

- no production Case/root-cause special branch exists;
- all relevant unit and integration tests pass;
- every live lane is diagnosed or honestly inconclusive from a persisted formal
  chain;
- decisive source-backed facts are preserved through RCA and final rendering;
- entity identity is exact and LLM-independent;
- claim validation is persisted and fail-closed;
- the final report cannot contradict formal RCA;
- N=10 preserves evidence and diagnosis quality; its latency and critical path
  are measured and reported, not used to waive correctness;
- an independent reviewer accepts both implementation and live results.
