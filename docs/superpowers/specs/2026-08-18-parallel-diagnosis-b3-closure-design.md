# Parallel Diagnosis B3 Closure Design

## 1. Status and scope

Status: approved direction B, detailed closure design for implementation.

This change closes the defects proven by the frozen `11.0.109` live series in
the multi-anomaly path:

```text
layer -> parallel_evidence -> conclusion
```

The change does not redesign the graph, add a global RCA, or encode known
Cases. The existing single-anomaly path remains unchanged and is exercised as
a regression control. Shared contracts may gain backward-compatible fields,
but new publication gates are activated by a persisted parallel lane envelope.

The release is accepted only after one frozen build is deployed with
`make delete`, `make build`, `make push`, and `make deploy`, followed by real
baseline, N=1, N=3, N=5, and N=10 runs using the same request. No product code,
prompt, manifest, Case, or acceptance rule may change between those runs.

## 2. Live evidence and root causes

The design addresses six independently observed defects.

### 2.1 Outer lifecycle is corrupted by inner lane events

Each parallel lane reuses `EvidenceCollectorNode` and `RootCauseAnalyzerNode`.
Their thinking events retain node names `evidence` and `rca`. The executor
interprets those names as outer LangGraph node transitions and archives the
outer `parallel_evidence` node before its lifecycle `end` event supplies
`group_results`. That produces a durable base output with `group_count=0`
while complete per-lane artifacts exist elsewhere.

The root cause is lifecycle namespace collision, not failed evidence
collection and not JSON serialization.

### 2.2 A count limit is incorrectly treated as a lane-fatal invariant

`build_selection_manifest()` marks all eligible support and required context
Facts as mandatory and raises when their count exceeds 48. In N=10, one lane
had 63 such Facts. The full snapshot existed, but the exception escaped before
RCA and before terminal artifact persistence.

The root cause is conflating lossless snapshot retention with bounded model
input. The full Fact index is authoritative; the RCA view is necessarily a
selection and must account for omissions instead of requiring every candidate
to fit.

### 2.3 The fan-in is partial but reported as successful

The parallel node converts a failed future into an in-memory fallback without
persisting the same artifact contract as successful lanes. The join filters
`None`, computes success from lanes without an error string, and can continue
to conclusion with fewer outputs than inputs.

The root cause is absence of a total-join invariant.

### 2.4 Source-backed logs have two truth paths

Elasticsearch or an observability query can populate the canonical logging
ledger. A scoped current/previous container log result can remain only in the
supplementary tool stream. The narrative can read that result, while the
deterministic dimension table sees only the canonical ledger and reports
Logging absent.

The root cause is normalizing by tool path rather than by observation
semantics and authoritative entity scope.

### 2.5 Fact membership is not claim entailment

The current claim gate proves that cited Fact IDs exist, belong to the lane,
and have sufficient directness/confidence. It does not prove that the cited
attribute and value are the proposition being published. Exit status, a
resource limit, and a restart event can therefore be combined into a different
cause that no Fact actually states.

The root cause is a free-text root-cause claim with citations, rather than an
open-world proposition that can be resolved back to exact Fact paths/values.

### 2.6 Validated and displayed support sets can diverge

Claim validation, entity summary construction, and final projection each
select supporting Fact IDs. A later projection can silently reduce the set,
leaving two different answers to “which Facts authorize this diagnosis?”

The root cause is multiple owners of the primary support set.

## 3. Considered approaches

### 3.1 Envelope and overflow patch only

This would make every lane visible and stop the N=10 omission. It would not
prevent a legally cited but semantically unsupported diagnosis or the split
logging truth.

Decision: rejected as insufficient for the observed false diagnosis.

### 3.2 B3 total lane contract plus open-world propositions

Keep the current graph and lane workers. Make the outer lifecycle namespace,
selection, terminal artifacts, global join, source normalization, claim
publication, and final support set deterministic. Represent a root-cause
claim as a reference to an arbitrary canonical Fact attribute and JSON value,
so new sources and previously unseen fields do not require a closed enum.

Decision: selected. It fixes the observed causal boundaries without a new RCA
engine or scenario registry.

### 3.3 Replace the workflow with a deterministic anomaly engine

This would require maintaining rules for Kubernetes reasons, metric names,
application messages, and workload types. It would be stable only for known
patterns and violate the no-special-case constraint.

Decision: rejected.

## 4. Non-negotiable invariants

### 4.1 No scenario policy

Production logic must not branch on:

- Case ID or test namespace;
- workload, Deployment, Pod, or container name;
- a known root-cause label;
- a literal error message, Kubernetes reason, exit code, or metric name;
- expected N=1/N=3/N=5/N=10 output.

Fixtures may contain concrete examples. Production decisions use only source
contracts, exact entity identity, Fact metadata, structured attribute/value,
quality, dimension, provenance, and deterministic ordering.

### 4.2 One input lane, one terminal artifact

For the ordered input lane inventory `L`, the ordered terminal artifact
inventory `T` must satisfy:

```text
len(T) == len(L)
set(T.group_id) == set(L.group_id)
T is ordered by presentation_index, then group_id
```

Each lane ends in exactly one state:

- `diagnosed`: a validated authoritative proposition exists;
- `inconclusive`: collection completed, but no claim passed publication;
- `error`: the lane could not produce or persist a trustworthy snapshot.

No lane is filtered out. A global response may still render the other lanes,
but its completeness section must list every non-diagnosed lane and reason.

### 4.3 Snapshot is lossless; model input is bounded

The canonical `EntityEvidenceSnapshot.fact_index` retains every accepted
whole Fact record. Selection never deletes from the snapshot. The bounded RCA
view contains representative whole records and a complete manifest for every
selected and omitted ID.

### 4.4 One owner of published support

The claim validator produces `validated_supporting_fact_ids`. That exact
ordered set is copied into the selected RCA, lane final projection, entity
summary, and deterministic report card. A UI display subset, if needed, is a
separate `displayed_supporting_fact_ids` field and cannot replace the validated
set.

### 4.5 Free text is explanatory, not authoritative

The LLM can propose labels, causal-chain prose, alternatives, and remediation.
The authoritative root-cause row is rendered from a validated proposition and
its resolved canonical Fact. If a model label disagrees with the proposition,
the Fact projection wins and the free-text label is not published as fact.

## 5. Contracts

### 5.1 SelectionManifest v2

The existing manifest gains explicit accounting:

```json
{
  "contract_version": "aiops.selection-manifest.v2",
  "max_facts": 48,
  "total_fact_count": 63,
  "eligible_support_fact_ids": [],
  "required_context_fact_ids": [],
  "rca_input_fact_ids": [],
  "omitted_fact_ids": [],
  "omission_reasons": {
    "fact-id": "equivalent_observation|lower_priority_within_dimension|rca_fact_count_limit"
  },
  "representative_of": {
    "selected-fact-id": ["selected-fact-id", "equivalent-id"]
  },
  "overflowed": true,
  "unselected_higher_priority_causal_fact_ids": []
}
```

`eligible_support_fact_ids` describes the full snapshot, not only selected
records. `rca_input_fact_ids` describes the model view. This distinction lets
the publication gate detect a model conclusion that ignored a stronger
omitted causal candidate.

### 5.2 Open-world EvidenceProposition

The proposition schema does not enumerate anomaly types or known fields:

```json
{
  "proposition_id": "prop-<deterministic digest>",
  "subject_entity_id": "k8s.pod:namespace/name:uid",
  "fact_id": "fact-...",
  "attribute": "exact FactRecord.attribute",
  "value_pointer": "/reason",
  "operator": "observed|equals|contains|gt|gte|lt|lte",
  "expected_value": "exact scalar or bounded JSON value",
  "relation": "causal|corroborating|contradicting|context"
}
```

`value_pointer` is an RFC 6901 JSON Pointer relative to `FactRecord.value`.
An empty pointer addresses the full scalar/value. `attribute` and the resolved
value come from arbitrary canonical Facts, so a new metric, log field, span
attribute, event structure, or custom tool can participate without changing a
central anomaly schema.

The model proposes the binding. Deterministic code resolves and verifies it.
It may correct the lane entity to the already-authoritative single-Pod scope,
but it never guesses a Fact, pointer, operator, or value.

### 5.3 ClaimValidation v2

```json
{
  "contract_version": "aiops.claim-validation.v2",
  "valid": true,
  "diagnostic_status": "diagnosed",
  "primary_proposition_id": "prop-...",
  "validated_propositions": [],
  "validated_supporting_fact_ids": [],
  "validated_contradicting_fact_ids": [],
  "unaccounted_causal_fact_ids": [],
  "invalid_bindings": [],
  "reasons": []
}
```

A diagnosed result requires:

1. one primary proposition scoped to the authoritative lane entity;
2. exact Fact ID, attribute, JSON Pointer, operator, and expected-value
   verification;
3. the primary proposition to use a direct, source-backed causal candidate;
4. every supporting/contradicting ID to pass the existing identity and quality
   gates;
5. no higher-priority direct causal candidate to be silently ignored;
6. the top-level support IDs to equal the union of validated causal and
   corroborating proposition Fact IDs.

If a legacy model output contains no propositions, parallel lanes receive one
bounded repair attempt with the proposition schema. It cannot be published as
`diagnosed` merely because legacy Fact membership passed. After the repair,
failure is `inconclusive` with exact reasons.

### 5.4 LaneDiagnosisArtifact v2

```json
{
  "contract_version": "aiops.lane-diagnosis-artifact.v2",
  "group_id": "g3-p2",
  "parent_group_id": "g3",
  "presentation_index": 4,
  "terminal_status": "diagnosed|inconclusive|error",
  "authoritative_entities": [],
  "artifact_refs": {
    "snapshot": {},
    "selection_manifest": {},
    "rca_input": {},
    "rca_attempts": {},
    "selected_rca": {},
    "claim_validation": {},
    "final_projection": {},
    "terminal_error": {}
  },
  "artifact_ref": {}
}
```

All components exist for every terminal state. Empty/error components are
explicit JSON objects with reason and stage, not missing files.

### 5.5 ParallelEvidenceOutput v2

```json
{
  "contract_version": "aiops.parallel-evidence-output.v2",
  "expected_group_count": 10,
  "terminal_group_count": 10,
  "join_complete": true,
  "diagnosed_count": 7,
  "inconclusive_count": 2,
  "error_count": 1,
  "groups": [
    {
      "group_id": "g1",
      "presentation_index": 0,
      "terminal_status": "diagnosed",
      "authoritative_entities": [],
      "artifact_ref": {},
      "snapshot_ref": {},
      "claim_validation_ref": {},
      "final_projection_ref": {}
    }
  ],
  "errors": []
}
```

The envelope is persisted only after every future has a terminal result. The
conclusion consumes this ordered inventory instead of rediscovering lanes from
free-form summaries.

## 6. Deterministic algorithms

### 6.1 Lifecycle namespace isolation

The scoped lane event wrapper retains the inner stage in `lane_stage` and sets
the event's outer lifecycle node to `parallel_evidence`. The executor uses only
the outer node for start/end accounting. SSE rendering can display `lane_stage`
and `group_id`, but a nested collector/RCA message cannot finish or start a
LangGraph node.

The lifecycle `end` event remains the only completion signal and carries the
actual `state_update`. Executor archival occurs after merging that update.

### 6.2 Diversity-preserving overflow reduction

Facts are ordered by existing generic quality plus stable identity. Before the
global fill, the reducer allocates slots in this order:

1. strongest direct causal candidate per entity and distinct
   `(dimension, fact_type, attribute)` signature;
2. strongest direct contradicting/negative observation per signature;
3. strongest direct record per available required dimension;
4. strongest configuration/context record per signature;
5. remaining records by stable quality order, round-robin across dimensions.

Repeated observations with the same entity, dimension, fact type, attribute,
canonical value digest, directness, and source system form an equivalence
class. The representative remains a complete immutable Fact. Other IDs remain
in the snapshot and appear under `representative_of` and `omission_reasons`.

The reducer never raises because a count exceeds the model budget. If it cannot
represent every distinct higher-priority causal signature, it records those
IDs in `unselected_higher_priority_causal_fact_ids`; a diagnosed publication is
then forbidden, but the lane artifact is still complete and inconclusive.

### 6.3 Source-semantic log normalization

Every successful, exactly scoped tool observation enters one common adapter:

```text
tool result
  -> validated lane/entity context
  -> source capability/dimension
  -> canonical whole FactRecord
  -> deduplicate by canonical content digest
  -> append to the lane snapshot ledger
```

A container-log observation is logging evidence whether it came from an
observability query, Kubernetes current logs, Kubernetes previous logs, or a
future tool declaring the same source capability. Tool names are adapter
metadata, not anomaly policy. A failed command, parser error, or identity-less
result becomes a limitation/error state and is never promoted as log content.

Coverage has three separately retained facts:

- source queried successfully and returned matching records;
- source queried successfully and returned no records;
- query/tool/parser failed.

One empty follow-up cannot erase a present result from another source.

### 6.4 Proposition resolution

For each proposed proposition, code:

1. resolves `fact_id` in the immutable snapshot;
2. verifies the Fact belongs to the lane entity;
3. requires `attribute` to exactly equal the Fact attribute;
4. resolves `value_pointer` with strict RFC 6901 rules;
5. applies the operator with type-safe semantics and no coercion from unrelated
   strings;
6. checks relation-specific quality (`causal` requires direct causal evidence);
7. generates `proposition_id` from the canonical resolved payload;
8. records success or the exact invalid binding.

There is no substring comparison between a Case label and a Fact. The optional
`contains` operator operates only on the explicitly selected Fact value and is
not sufficient by itself for a primary causal proposition unless the Fact is
already a direct causal candidate.

### 6.5 Final projection

The lane finalizer is the only writer of authoritative entity summaries. It
copies the claim gate's status, primary proposition, support set,
contradictions, and reasons. The conclusion formatter renders those fields and
then appends snapshot dimension cards. It may request an LLM narrative, but
the narrative cannot replace or remove deterministic cards.

## 7. Agent versus code responsibilities

The Agent may:

- plan bounded, scoped follow-up queries after mandatory collection;
- propose Fact-bound open-world propositions;
- order validated propositions into a causal explanation;
- describe alternatives, unknowns, and remediation;
- perform at most one schema repair after deterministic feedback.

Deterministic code must:

- create lane inventory and exact namespace/name/UID scope;
- execute the minimum source plan and account for each source result;
- normalize Facts from every source-backed tool observation;
- retain the lossless snapshot and select the bounded RCA view;
- persist every terminal lane and the complete ordered fan-in;
- resolve proposition paths and values;
- enforce evidence quality, competitor accounting, and support-set equality;
- render the authoritative root-cause proposition and dimension tables;
- cap retries, model rounds, and tool budgets.

This boundary lets a small model contribute semantic reasoning without owning
identity, retention, validation, completeness, or final factual publication.

## 8. Failure behavior

- Collector failure before snapshot: persist an `error` lane with the exact
  stage/error and empty authoritative components.
- Snapshot failure: persist an `error` lane; do not publish RCA.
- Selection overflow: reduce and account; never throw solely due to count.
- Unrepresented stronger causal candidate: persist `inconclusive`.
- Model parse/schema failure: one bounded repair; then `inconclusive`.
- Invalid Fact/entity/path/value/operator: `inconclusive` with binding reasons.
- Archive write/hash failure: terminal `error`; no diagnosis.
- One lane error: join remains total and report remains available, with global
  `join_complete=true` only if all expected terminal artifacts are present.
- Outer lifecycle mismatch: fail the parallel node rather than persist a zero-
  group success envelope.
- Narrative failure: deterministic entity cards and dimension evidence remain.

## 9. Focused code boundaries

Expected modifications are intentionally limited:

- `app/core/workflow/nodes/parallel_evidence.py`
  - scoped lifecycle namespace, terminal lane creation, total join, and final
    support projection;
- `app/core/workflow/entity_evidence_snapshot.py`
  - SelectionManifest v2 and non-throwing diversity reducer;
- `app/core/workflow/lane_diagnosis_artifact.py`
  - terminal status and error-safe complete artifact envelope;
- `app/core/workflow/fact_contract.py`
  - open-world proposition model/resolver and source-semantic Fact adapter;
- `app/core/workflow/schemas.py`
  - backward-compatible proposition/claim fields;
- `app/core/workflow/nodes/root_cause_analyzer.py`
  - parallel-lane proposition prompt payload and one repair pass;
- `app/core/workflow/executor.py`
  - outer lifecycle guard and ParallelEvidenceOutput v2 projection;
- `app/core/workflow/nodes/conclusion_formatter.py`
  - authoritative proposition rendering and exact validated support set;
- focused unit/replay tests under `tests/unit/workflow/` and `tests/replay/`.

No Case manifest, deployment topology, observability backend, or remediation
code is in scope.

## 10. Test strategy and acceptance

### 10.1 TDD unit contracts

Tests must be written and observed failing before production changes:

1. nested lane events cannot change the outer node lifecycle;
2. 63+ eligible Facts produce a complete manifest, not an exception;
3. overflow retains dimension/signature diversity and accounts for every ID;
4. every input lane produces a verified terminal artifact, including errors;
5. a global envelope has exact ordered lane cardinality and reloadable hashes;
6. an exactly scoped previous-log observation enters Logging even when another
   log query is empty;
7. identity-less or failed log output is not promoted;
8. a claim whose attribute/value proposition does not match its Fact is
   inconclusive;
9. a valid arbitrary previously unseen attribute/value proposition passes;
10. an ignored stronger causal candidate prevents diagnosed publication;
11. claim, artifact, entity summary, and report have the same validated support
    IDs;
12. legacy single-path tests remain green.

### 10.2 Replay acceptance

Archived `11.0.109` lanes are replayed without network access:

- N=10 c05 must produce an explicit terminal result and never disappear;
- N=5 c10 must not publish the unsupported free-text cause; it must either bind
  an exact source proposition or be inconclusive;
- c07/c09 source-backed previous/current logs must not coexist with a false
  `Logging absent` state;
- N=3 support IDs must remain identical across validation and final projection;
- base parallel output must contain every lane in deterministic order.

Concrete fixture content proves generic behavior; production code may not
inspect fixture identifiers or literals.

### 10.3 Frozen real deployment

After unit and replay suites pass:

1. increment `VERSION` once;
2. run `make delete`, `make build`, `make push`, `make deploy`;
3. prove backend, MCP, and frontend services are healthy and mutually
   reachable;
4. freeze the deployed image digest and fixed request;
5. run baseline, N=1 controls, N=3, N=5, and N=10 once each;
6. record each run ID, wall time, model/tool call counts, exact lane inventory,
   terminal status, UID, four-dimensional coverage, proposition validation,
   support continuity, and artifact hashes;
7. independently review each run and the cross-run matrix.

Acceptance requires no silent lane omission, no zero-group base handoff, no
false absent state when canonical source-backed data exists, no diagnosis
without a validated exact proposition, and no support-set divergence. A real
run may be inconclusive when evidence is insufficient; correctness is preferred
to a guessed diagnosis.
