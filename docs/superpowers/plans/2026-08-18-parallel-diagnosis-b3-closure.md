# Parallel Diagnosis B3 Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the multi-anomaly path persist every lane, preserve useful source-backed evidence through bounded selection, publish only Fact-bound root-cause propositions, and render one consistent support set without scenario-specific rules.

**Architecture:** Keep `layer -> parallel_evidence -> conclusion`. Isolate nested lane event names from the outer lifecycle, retain a lossless snapshot with a deterministic bounded selection manifest, persist one terminal artifact per lane, validate open-world Fact attribute/value propositions, and fan in through a durable ordered envelope. The single-anomaly topology is unchanged and serves as a regression control.

**Tech Stack:** Python 3.11, Pydantic v2, LangGraph state, pytest, Kubernetes, Docker/Make, existing `ContextArchive` SHA-256 references.

---

## File structure

Create focused modules instead of expanding the already large Fact and node
files:

- `app/core/workflow/evidence_proposition.py`: open-world proposition schema,
  RFC 6901 resolution, typed operators, and lane claim validation.
- `app/core/workflow/tool_observation_fact.py`: normalize exactly scoped
  source-backed tool observations into canonical Fact Ledgers.
- `tests/unit/workflow/test_evidence_proposition.py`: proposition contract
  unit tests.
- `tests/unit/workflow/test_tool_observation_fact.py`: source-semantic tool
  normalization unit tests.
- `tests/replay/test_b3_parallel_closure.py`: frozen `11.0.109` regression
  replay assertions.

Modify existing focused owners:

- `app/core/workflow/entity_evidence_snapshot.py`: manifest v2 reducer.
- `app/core/workflow/lane_diagnosis_artifact.py`: terminal artifact v2.
- `app/core/workflow/nodes/parallel_evidence.py`: lifecycle scope, total join,
  terminal artifacts, proposition gate, exact final support set.
- `app/core/workflow/nodes/root_cause_analyzer.py`: proposition input/schema and
  one bounded repair for parallel lanes.
- `app/core/workflow/executor.py`: outer lifecycle guard and v2 envelope.
- `app/core/workflow/nodes/conclusion_formatter.py`: deterministic proposition
  and support rendering.
- `app/core/workflow/schemas.py`: backward-compatible RCA proposition fields.

## Task 1: Isolate nested lane events from the outer lifecycle

**Files:**

- Modify: `app/core/workflow/nodes/parallel_evidence.py`
- Modify: `app/core/workflow/stream_contract.py`
- Test: `tests/unit/workflow/test_parallel_evidence_stream.py`
- Test: `tests/unit/workflow/test_executor_timing.py`

- [ ] **Step 1: Write the failing scoped-event test**

Add a test that wraps an inner event whose original node is `rca` and asserts
that the outer node is `parallel_evidence` while the inner stage survives:

```python
def test_scoped_lane_event_keeps_outer_lifecycle_node():
    target = Queue()
    queue = _ScopedParallelEventQueue(
        target,
        group_id="g1",
        entities=[{"kind": "Pod", "namespace": "ns", "name": "pod"}],
    )
    queue.put(("thinking", {"node": "rca", "type": "ai_message"}))

    tag, event = target.get_nowait()
    assert tag == "thinking"
    assert event["node"] == "parallel_evidence"
    assert event["lane_stage"] == "rca"
    assert event["parallel_context"]["group_id"] == "g1"
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
pytest -q tests/unit/workflow/test_parallel_evidence_stream.py -k outer_lifecycle_node
```

Expected: FAIL because the current wrapper preserves `node=rca` and has no
`lane_stage`.

- [ ] **Step 3: Implement minimal event namespace isolation**

In `_ScopedParallelEventQueue._decorate()`, preserve the inner node and replace
only the outer lifecycle key:

```python
inner_stage = str(item[1].get("node") or "").strip()
decorated = {
    **item[1],
    "node": "parallel_evidence",
    "parallel_context": copy.deepcopy(self._parallel_context),
}
if inner_stage:
    decorated["lane_stage"] = inner_stage
return item[0], decorated
```

Project `lane_stage` through `project_parallel_tool_event()` without using it
for executor lifecycle accounting.

- [ ] **Step 4: Add an executor regression test**

Feed a scoped thinking event between `parallel_evidence` lifecycle start/end
and assert `_archive_node_transition()` receives the state update containing
three groups, not an early empty snapshot.

- [ ] **Step 5: Run focused tests and verify GREEN**

```bash
pytest -q tests/unit/workflow/test_parallel_evidence_stream.py tests/unit/workflow/test_executor_timing.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/core/workflow/nodes/parallel_evidence.py app/core/workflow/stream_contract.py tests/unit/workflow/test_parallel_evidence_stream.py tests/unit/workflow/test_executor_timing.py
git commit -m "fix: isolate parallel lane lifecycle events"
```

## Task 2: Replace fatal Fact overflow with SelectionManifest v2

**Files:**

- Modify: `app/core/workflow/entity_evidence_snapshot.py`
- Test: `tests/unit/workflow/test_context_handoff.py`
- Test: `tests/unit/workflow/test_rca_artifacts.py`

- [ ] **Step 1: Write failing overflow and accounting tests**

Construct 63 direct records across Kubernetes, metrics, logging, and tracing.
Assert:

```python
manifest = build_selection_manifest(fact_index, max_facts=48)
payload = manifest.to_dict()
assert payload["contract_version"] == "aiops.selection-manifest.v2"
assert len(payload["rca_input_fact_ids"]) == 48
assert set(payload["rca_input_fact_ids"]) | set(payload["omitted_fact_ids"]) == set(fact_index)
assert set(payload["rca_input_fact_ids"]).isdisjoint(payload["omitted_fact_ids"])
assert payload["overflowed"] is True
assert set(payload["omission_reasons"]) == set(payload["omitted_fact_ids"])
assert {fact_index[f]["dimension"] for f in payload["rca_input_fact_ids"]} == {
    "kubernetes", "metrics", "logging", "tracing"
}
```

Add a second test with repeated canonical content and assert one representative
is selected while every equivalent Fact ID remains accounted for.

- [ ] **Step 2: Run and verify RED**

```bash
pytest -q tests/unit/workflow/test_context_handoff.py -k 'selection_manifest and (overflow or equivalent)'
```

Expected: FAIL with `MandatoryEvidenceBudgetError` or missing v2 fields.

- [ ] **Step 3: Implement the v2 immutable contract**

Replace the exception path with a frozen `SelectionManifest` containing:

```python
contract_version: str
max_facts: int
total_fact_count: int
eligible_support_fact_ids: tuple[str, ...]
required_context_fact_ids: tuple[str, ...]
rca_input_fact_ids: tuple[str, ...]
omitted_fact_ids: tuple[str, ...]
omission_reasons: Mapping[str, str]
representative_of: Mapping[str, tuple[str, ...]]
overflowed: bool
unselected_higher_priority_causal_fact_ids: tuple[str, ...]
```

Use stable content digests over entity, dimension, fact type, attribute,
canonical JSON value, directness, and source system. Allocate representative
slots per `(entity, dimension, fact_type, attribute)` before stable
round-robin fill. Never mutate or remove records from `fact_index`.

- [ ] **Step 4: Preserve backward-compatible readers**

Keep the existing five list/map keys unchanged so current RCA input builders
continue working. Remove only the count-based raise; retain
`MandatoryEvidenceBudgetError` temporarily if another trust-boundary use still
requires it.

- [ ] **Step 5: Run focused tests and verify GREEN**

```bash
pytest -q tests/unit/workflow/test_context_handoff.py tests/unit/workflow/test_rca_artifacts.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/core/workflow/entity_evidence_snapshot.py tests/unit/workflow/test_context_handoff.py tests/unit/workflow/test_rca_artifacts.py
git commit -m "fix: account for RCA fact overflow deterministically"
```

## Task 3: Persist a terminal artifact for every lane

**Files:**

- Modify: `app/core/workflow/lane_diagnosis_artifact.py`
- Modify: `app/core/workflow/nodes/parallel_evidence.py`
- Test: `tests/unit/workflow/test_lane_diagnosis_artifact.py`
- Test: `tests/unit/workflow/test_parallel_evidence.py`

- [ ] **Step 1: Write failing v2 artifact tests**

Persist and reload an error artifact with empty explicit components:

```python
artifact = writer.persist_terminal(
    group_id="g5",
    parent_group_id="g5",
    presentation_index=4,
    terminal_status="error",
    authoritative_entities=[{"namespace": "ns", "name": "pod"}],
    components={
        "snapshot": {},
        "selection_manifest": {},
        "rca_input": {},
        "rca_attempts": [],
        "selected_rca": {},
        "claim_validation": {"valid": False},
        "final_projection": {"diagnostic_status": "error"},
        "terminal_error": {"stage": "snapshot", "message": "boom"},
    },
)
loaded = writer.reload_and_verify(artifact)
assert artifact["terminal_status"] == "error"
assert set(loaded) >= set(artifact["artifact_refs"]) | {"artifact"}
```

- [ ] **Step 2: Run and verify RED**

```bash
pytest -q tests/unit/workflow/test_lane_diagnosis_artifact.py -k terminal
```

Expected: FAIL because v1 only accepts diagnosed/inconclusive and has no
terminal error component.

- [ ] **Step 3: Implement v2 writer and backward-compatible reload**

Add `terminal_status: Literal["diagnosed", "inconclusive", "error"]`, require
all eight component references, and retain the v1 loader for archived replay.
`persist()` may delegate to `persist_terminal()` for successful legacy calls.

- [ ] **Step 4: Make the parallel future exception path persist an error lane**

Introduce one helper whose inputs are only the lane inventory, archive run ID,
stage, and exception. It must write the complete v2 artifact and return the
same group-result shape consumed by conclusion. Do not use error-message
content to choose behavior.

- [ ] **Step 5: Assert total join cardinality**

Add a test with three lanes where the middle worker raises. Assert:

```python
assert len(result["group_results"]) == 3
assert [g["group_id"] for g in result["group_results"]] == ["g1", "g2", "g3"]
assert result["group_results"][1]["terminal_status"] == "error"
assert result["group_results"][1]["lane_diagnosis_artifact_ref"]
```

- [ ] **Step 6: Run focused tests and verify GREEN**

```bash
pytest -q tests/unit/workflow/test_lane_diagnosis_artifact.py tests/unit/workflow/test_parallel_evidence.py
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add app/core/workflow/lane_diagnosis_artifact.py app/core/workflow/nodes/parallel_evidence.py tests/unit/workflow/test_lane_diagnosis_artifact.py tests/unit/workflow/test_parallel_evidence.py
git commit -m "fix: persist every parallel lane terminal state"
```

## Task 4: Persist and validate the ordered total fan-in

**Files:**

- Modify: `app/core/workflow/executor.py`
- Modify: `app/core/workflow/state.py`
- Test: `tests/unit/workflow/test_executor_timing.py`
- Test: `tests/unit/workflow/test_parallel_evidence.py`

- [ ] **Step 1: Write a failing v2 envelope test**

Build three terminal groups in scrambled completion order and assert:

```python
snapshot = executor._extract_state_snapshot(state, "parallel_evidence")
assert snapshot["contract_version"] == "aiops.parallel-evidence-output.v2"
assert snapshot["expected_group_count"] == 3
assert snapshot["terminal_group_count"] == 3
assert snapshot["join_complete"] is True
assert [g["group_id"] for g in snapshot["groups"]] == ["g1", "g2", "g3"]
assert all(g["artifact_ref"] for g in snapshot["groups"])
```

Add failure tests for duplicate, missing, and unexpected group IDs. Such a join
must be `join_complete=false` and list deterministic errors; it must never
silently report success.

- [ ] **Step 2: Run and verify RED**

```bash
pytest -q tests/unit/workflow/test_executor_timing.py -k parallel_snapshot
```

Expected: FAIL because the current envelope is v1 and has no expected count or
join invariant.

- [ ] **Step 3: Store expected lane inventory in state**

`ParallelEvidenceNode.execute()` writes a compact inventory before fan-out and
returns it with terminal results:

```python
parallel_lane_inventory = [
    {"group_id": gid, "presentation_index": index,
     "entities": authoritative_entities}
    for index, lane in enumerate(groups)
]
```

Add the optional typed state field and use it only for join validation.

- [ ] **Step 4: Implement the v2 projection**

Build counts from terminal statuses, compare expected and terminal ID sets,
include component refs/hashes, and order by `presentation_index, group_id`.
Never read summary text to construct the envelope.

- [ ] **Step 5: Run focused tests and verify GREEN**

```bash
pytest -q tests/unit/workflow/test_executor_timing.py tests/unit/workflow/test_parallel_evidence.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/core/workflow/executor.py app/core/workflow/state.py app/core/workflow/nodes/parallel_evidence.py tests/unit/workflow/test_executor_timing.py tests/unit/workflow/test_parallel_evidence.py
git commit -m "fix: persist complete ordered parallel handoff"
```

## Task 5: Normalize source-backed tool observations into the common ledger

**Files:**

- Create: `app/core/workflow/tool_observation_fact.py`
- Modify: `app/core/workflow/entity_evidence_snapshot.py`
- Test: `tests/unit/workflow/test_tool_observation_fact.py`
- Test: `tests/unit/workflow/test_group_evidence.py`

- [ ] **Step 1: Write failing present-plus-empty logging tests**

Use two exactly scoped events for the same Pod: one source-backed non-empty
logging observation and one successful empty follow-up. Assert the resulting
ledger contains the non-empty Fact and aggregate coverage remains `present`.

Also test that an identity-less result and a failed command produce limitations
but no log Fact.

- [ ] **Step 2: Run and verify RED**

```bash
pytest -q tests/unit/workflow/test_tool_observation_fact.py
```

Expected: FAIL because the module/API does not exist.

- [ ] **Step 3: Implement a capability-driven adapter**

Expose:

```python
def build_tool_observation_fact_ledgers(
    events: Sequence[Mapping[str, Any]],
    *,
    authoritative_entities: Sequence[Mapping[str, Any]],
) -> ToolObservationFactResult:
    ...
```

The result contains `fact_ledgers`, `limitations`, and coverage observations.
Determine dimension from validated `evidence_context.dimension`, structured
`dimension`, or a central tool capability registry. Require exact
namespace/name match and successful semantic status before promoting content.
Use raw/structured archive refs as provenance. Deduplicate canonical content
by digest but retain source/count/time metadata.

- [ ] **Step 4: Merge adapter ledgers into snapshot construction**

Merge native MCP ledgers and tool-observation ledgers before building the Fact
index. Apply the existing collision and entity-scope checks uniformly. Do not
let an empty observation remove existing Facts.

- [ ] **Step 5: Run focused tests and verify GREEN**

```bash
pytest -q tests/unit/workflow/test_tool_observation_fact.py tests/unit/workflow/test_group_evidence.py tests/unit/workflow/test_context_handoff.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/core/workflow/tool_observation_fact.py app/core/workflow/entity_evidence_snapshot.py tests/unit/workflow/test_tool_observation_fact.py tests/unit/workflow/test_group_evidence.py tests/unit/workflow/test_context_handoff.py
git commit -m "fix: normalize scoped tool observations into fact ledgers"
```

## Task 6: Add open-world proposition validation

**Files:**

- Create: `app/core/workflow/evidence_proposition.py`
- Modify: `app/core/workflow/schemas.py`
- Test: `tests/unit/workflow/test_evidence_proposition.py`

- [ ] **Step 1: Write failing arbitrary-field and mismatch tests**

Create a Fact whose never-before-seen attribute is
`vendor.runtime.custom_state` and value is `{"phase": "blocked", "code": 731}`.
Assert `value_pointer=/code`, `operator=equals`, `expected_value=731` validates.

With the same Fact, assert `expected_value=137` fails. Assert a proposition
with the wrong attribute or a foreign entity fails. Assert a causal relation
on a context-only Fact fails.

- [ ] **Step 2: Run and verify RED**

```bash
pytest -q tests/unit/workflow/test_evidence_proposition.py
```

Expected: FAIL because the module/API does not exist.

- [ ] **Step 3: Implement strict proposition models**

Add Pydantic models equivalent to:

```python
class EvidenceProposition(BaseModel):
    proposition_id: str = ""
    subject_entity_id: str
    fact_id: str
    attribute: str
    value_pointer: str = ""
    operator: Literal["observed", "equals", "contains", "gt", "gte", "lt", "lte"]
    expected_value: Any = None
    relation: Literal["causal", "corroborating", "contradicting", "context"]
```

Implement strict RFC 6901 unescaping (`~0`, `~1`), mapping/list traversal, typed
numeric comparisons, exact equality, and bounded string/list containment.
Generate the proposition ID from the resolved canonical payload rather than
trusting a model-supplied ID.

- [ ] **Step 4: Implement lane claim validation**

Expose:

```python
def validate_lane_claim_propositions(
    rca: Mapping[str, Any],
    *,
    snapshot: Mapping[str, Any],
    authoritative_entity_ids: Sequence[str],
) -> dict[str, Any]:
    ...
```

Require one primary causal proposition for diagnosed publication, validate all
bindings, enforce existing Fact quality, reject unaccounted higher-priority
causal IDs from the manifest, and derive the one authoritative ordered support
set. Return `aiops.claim-validation.v2`; never alter snapshot Facts.

- [ ] **Step 5: Run focused tests and verify GREEN**

```bash
pytest -q tests/unit/workflow/test_evidence_proposition.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/core/workflow/evidence_proposition.py app/core/workflow/schemas.py tests/unit/workflow/test_evidence_proposition.py
git commit -m "feat: validate open world evidence propositions"
```

## Task 7: Gate parallel RCA and keep one exact support set

**Files:**

- Modify: `app/core/workflow/nodes/root_cause_analyzer.py`
- Modify: `app/core/workflow/nodes/parallel_evidence.py`
- Modify: `app/core/workflow/nodes/conclusion_formatter.py`
- Test: `tests/unit/workflow/test_parallel_evidence.py`
- Test: `tests/unit/workflow/test_conclusion_formatter.py`
- Test: `tests/unit/workflow/test_rca_artifacts.py`

- [ ] **Step 1: Write a failing unsupported-claim test**

Provide valid Fact IDs for an exit symptom, resource configuration, restart
symptom, and a separate stronger causal event. Return a diagnosed legacy RCA
without a matching proposition. Assert the parallel finalizer makes it
inconclusive rather than publishing the free-text cause.

- [ ] **Step 2: Write a failing support-continuity test**

For a valid proposition with two support IDs, assert equality across:

```python
assert selected_rca["supporting_fact_ids"] == claim["validated_supporting_fact_ids"]
assert final_projection["supporting_fact_ids"] == claim["validated_supporting_fact_ids"]
assert entity_summary["supporting_fact_ids"] == claim["validated_supporting_fact_ids"]
assert rendered_card_fact_ids == claim["validated_supporting_fact_ids"]
```

- [ ] **Step 3: Run and verify RED**

```bash
pytest -q tests/unit/workflow/test_parallel_evidence.py tests/unit/workflow/test_conclusion_formatter.py -k 'proposition or support_continuity'
```

Expected: FAIL because legacy membership can publish diagnosed and projections
can choose support independently.

- [ ] **Step 4: Add proposition schema to bounded RCA input**

For parallel lanes, tell the model to return `propositions` and
`primary_proposition`. Include allowed Fact IDs and exact Facts already in the
bounded projection. Do not add Case examples, known reasons, metric examples,
or workload-specific prompt text.

- [ ] **Step 5: Apply one bounded repair and v2 validation**

After existing Fact membership validation, call the proposition gate. If the
legacy/invalid output has eligible causal evidence, the existing single repair
attempt receives only schema errors, authoritative identity, and the bounded
Facts. No new tools or broader scope are allowed. If it remains invalid, set
`diagnostic_status=inconclusive`.

- [ ] **Step 6: Make the claim gate the support owner**

Delete later re-selection. Copy the exact ordered validated support IDs to the
selected RCA, entity summary, final projection, and renderer. If the renderer
limits rows, write a separate display subset and retain the authoritative set.

- [ ] **Step 7: Render the authoritative proposition**

Render entity, source, attribute, operator/value, Fact ID, and provenance from
the resolved proposition. Place model prose under an explanatory label and do
not let it replace the authoritative row.

- [ ] **Step 8: Run focused tests and verify GREEN**

```bash
pytest -q tests/unit/workflow/test_parallel_evidence.py tests/unit/workflow/test_conclusion_formatter.py tests/unit/workflow/test_rca_artifacts.py
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add app/core/workflow/nodes/root_cause_analyzer.py app/core/workflow/nodes/parallel_evidence.py app/core/workflow/nodes/conclusion_formatter.py tests/unit/workflow/test_parallel_evidence.py tests/unit/workflow/test_conclusion_formatter.py tests/unit/workflow/test_rca_artifacts.py
git commit -m "fix: gate parallel diagnoses on resolved propositions"
```

## Task 8: Replay the frozen 11.0.109 failures

**Files:**

- Create: `tests/replay/test_b3_parallel_closure.py`
- Read only: `reports/live-validation/b2-11.0.109-20260817/`
- Read only: `agent-loop/authoritative-evidence-b2-live-validation-20260817/tasks/T006/attempts/A001/artifacts/`

- [ ] **Step 1: Add replay fixtures that point to copied immutable archives**

Load the copied N=3/N=5/N=10 artifacts by relative path. Do not query the
cluster or alter archived files. Recompute and assert their existing SHA
manifest before using them.

- [ ] **Step 2: Add closure assertions**

Assert generic outcomes:

- every expected lane reaches a terminal result;
- selection overflow returns a manifest and artifact rather than raising;
- a legacy claim without an exact proposition cannot remain diagnosed;
- source-backed logging Facts keep Logging present despite an empty follow-up;
- validated support equals final support;
- global envelope order/cardinality match the input inventory.

- [ ] **Step 3: Run replay tests**

```bash
pytest -q tests/replay/test_b3_parallel_closure.py
```

Expected: PASS with no network access.

- [ ] **Step 4: Commit**

```bash
git add tests/replay/test_b3_parallel_closure.py
git commit -m "test: replay parallel diagnosis closure failures"
```

## Task 9: Run full local verification

**Files:** none beyond fixes required by failing in-scope regressions.

- [ ] **Step 1: Run all focused workflow tests**

```bash
pytest -q tests/unit/workflow
```

Expected: all tests pass.

- [ ] **Step 2: Run replay tests**

```bash
pytest -q tests/replay
```

Expected: all tests pass.

- [ ] **Step 3: Run repository lint/type/test targets available in Makefile**

First inspect exact non-mutating targets with `make help` and use the existing
test/check targets. Record every command and exit code. Do not run formatters
that rewrite unrelated user files.

- [ ] **Step 4: Inspect for forbidden policy**

```bash
git diff -- app/core/workflow | rg -n 'aiops-case|c0[1-9]|c10|c11|OOMKilled|Liveness|kube_pod_container_status_restarts_total'
```

Expected: no production-code additions containing scenario/fixture literals.
Test fixtures may contain concrete data.

- [ ] **Step 5: Review the complete diff and working tree**

```bash
git diff --check
git status --short
```

Expected: no whitespace errors; unrelated pre-existing user changes remain
untouched.

## Task 10: Build and deploy one frozen release

**Files:**

- Modify: `VERSION`
- Read: `Makefile`
- Read: deployment manifests referenced by Make targets.

- [ ] **Step 1: Capture the current deployed image and service health**

Record current backend/MCP/frontend Pods, images, digests, Services, endpoints,
and HTTP health into a new non-overwriting agent-loop attempt.

- [ ] **Step 2: Increment VERSION once**

Use the repository's existing version format. Do not modify deployment source
paths or replace registry references with permanent local-image changes.

- [ ] **Step 3: Execute the user's deployment sequence exactly**

Run separately and record wall time/exit code:

```bash
make delete
make build
make push
make deploy
```

Do not continue after a failed build, push, or deploy. Diagnose with read-only
commands before changing anything.

- [ ] **Step 4: Verify the deployed digest and three-component connectivity**

Use the actual resource names resolved from the Makefile/manifests. Prove:

- Pods are Ready and running the new immutable image digest;
- backend health returns HTTP 200;
- backend can load/reach all configured MCP servers;
- frontend Service returns HTTP 200 and can reach the backend;
- backend logs show the intended model configuration without exposing keys.

## Task 11: Run the frozen live validation matrix

**Files:**

- Create: a new `agent-loop/` attempt tree and immutable artifact manifests.
- Create: a new `reports/live-validation/` release directory through existing
  test/report scripts.

- [ ] **Step 1: Freeze the request, image digest, config hash, and Case set**

Use exactly:

```text
请诊断当前集群中的所有异常 Pod；对每个异常实体独立收集 Kubernetes、Metrics、Logging、Tracing 真实证据，基于 Fact ID 给出根因；证据不足时明确输出 inconclusive，不得猜测。
```

- [ ] **Step 2: Run baseline and record its independent wall time**

Clean all Case namespaces with the existing safe target, prove no abnormal Case
Pod remains, issue one backend `/ask`, and archive SSE/report/logs.

- [ ] **Step 3: Run N=1 controls independently**

Deploy/validate the preselected c08 and c07 controls one at a time, wait for
observability readiness using the existing validator, issue exactly one fixed
request per scenario, and record each wall time separately.

- [ ] **Step 4: Run N=3, N=5, and N=10 independently**

Use the same Case sets as the `11.0.109` frozen series, one clean scenario at a
time. Record deployment readiness time separately from `/ask` wall time. Do not
change code/config/prompts between scenarios.

- [ ] **Step 5: Audit each run before continuing**

For every run, verify exact expected/terminal lane IDs, namespace/name/UID,
dimension states, proposition resolution, validated support continuity,
artifact hashes, zero silent omissions, and any explicit inconclusive/error
reason. Record model-call count, tool cumulative time, tool critical path,
evidence-node time, and total wall time.

- [ ] **Step 6: Perform independent review and close the loop**

The reviewer returns `ACCEPT`, `REWORK`, or `BLOCKED` against every acceptance
criterion. Update board, metrics, decisions, lessons, and handoffs. Do not call
the goal complete unless all required evidence exists and the reviewer accepts
the cross-run result.
