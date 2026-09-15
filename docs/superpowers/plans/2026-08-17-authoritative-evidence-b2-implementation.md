# Authoritative Evidence B2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every single- and multi-Pod diagnosis use a reloadable authoritative evidence → formal RCA → claim-validation → deterministic-report chain that remains safe and useful with a small LLM, without Case-specific production logic.

**Architecture:** Keep the existing workflow graph and canonical Fact Ledger. Add a persisted lane artifact envelope, move exact identity and evidence selection under deterministic code, permit one generic constrained RCA repair attempt, and make conclusion rendering fail closed on formal claim validation. Optimize duplicated work only after correctness is proven; elapsed time is measured but is not a correctness gate.

**Tech Stack:** Python 3.12, Pydantic, LangGraph workflow state, pytest, Kubernetes, Docker/Make deployment, existing ContextArchive and Fact Ledger contracts.

---

## File map

- Create `app/core/workflow/lane_diagnosis_artifact.py`: typed reloadable lane artifact, hashes, and archive references.
- Modify `app/core/context/archive.py`: atomic JSON write helper and file digest/reload verification.
- Modify `app/core/workflow/entity_evidence_snapshot.py`: deterministic selection manifest and snapshot round trip.
- Modify `app/core/workflow/fact_contract.py`: generic evidence-role reconciliation, mandatory selection, and authoritative single-lane identity injection.
- Modify `app/core/workflow/nodes/root_cause_analyzer.py`: validated output persistence and one constrained repair attempt.
- Modify `app/core/workflow/nodes/parallel_evidence.py`: build/persist one artifact per lane and return ordered strong handoff.
- Modify `app/core/workflow/executor.py`: archive non-empty reloadable `parallel_evidence` output.
- Modify `app/core/workflow/nodes/conclusion_formatter.py`: deterministic formal-RCA authority for parallel and legacy paths.
- Modify `app/core/workflow/state.py`: type authoritative lane artifacts.
- Add focused tests under `tests/unit/context/` and `tests/unit/workflow/`.
- Add `tests/replay/workflow/test_authoritative_evidence_replay.py`: offline replay of retained generic artifacts.

## Task 1: Atomic reloadable lane artifacts

**Files:**

- Create: `app/core/workflow/lane_diagnosis_artifact.py`
- Modify: `app/core/context/archive.py`
- Create: `tests/unit/workflow/test_lane_diagnosis_artifact.py`
- Modify: `tests/unit/context/test_archive_budget_observation.py`

- [ ] **Step 1: Write the failing artifact round-trip test**

```python
def test_lane_artifact_round_trip_verifies_every_hash(tmp_path, monkeypatch):
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    writer = LaneDiagnosisArtifactWriter("run-g1")
    artifact = writer.persist(
        group_id="g1",
        parent_group_id="g1",
        presentation_index=0,
        authoritative_entities=[{
            "kind": "Pod", "namespace": "demo", "name": "api",
            "uid": "uid-api", "entity_id": "k8s.pod:demo/api:uid-api",
        }],
        snapshot={"contract_version": "aiops.entity-evidence-snapshot.v1"},
        rca_input={"fact_ledgers": []},
        rca_attempts=[],
        selected_rca={"diagnostic_status": "inconclusive"},
        claim_validation={"valid": False},
        final_projection={"diagnostic_status": "inconclusive"},
    )

    loaded = writer.reload_and_verify(artifact)
    assert loaded["snapshot"]["contract_version"] == (
        "aiops.entity-evidence-snapshot.v1"
    )
    assert all(ref["sha256"] for ref in artifact["artifact_refs"].values())
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_lane_diagnosis_artifact.py
```

Expected: import failure because `LaneDiagnosisArtifactWriter` does not exist.

- [ ] **Step 3: Implement the minimal artifact contract**

Implement a Pydantic/typed JSON envelope with:

```python
LANE_DIAGNOSIS_CONTRACT_VERSION = "aiops.lane-diagnosis-artifact.v1"

class LaneArtifactRef(BaseModel):
    path: str
    sha256: str
    bytes: int

class LaneDiagnosisArtifact(BaseModel):
    contract_version: Literal["aiops.lane-diagnosis-artifact.v1"]
    group_id: str
    parent_group_id: str
    presentation_index: int
    authoritative_entities: list[dict[str, Any]]
    artifact_refs: dict[str, LaneArtifactRef]
    diagnostic_status: Literal["diagnosed", "inconclusive"]
```

`ContextArchive.write_json_atomic()` must write a temporary file in the target
directory, flush/fsync, replace the final path, and return path/size/SHA-256.
`reload_and_verify()` must reject a missing file, digest mismatch, invalid JSON,
or contract mismatch.

- [ ] **Step 4: Run focused tests and verify GREEN**

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_lane_diagnosis_artifact.py \
  tests/unit/context/test_archive_budget_observation.py
```

Expected: PASS.

## Task 2: Deterministic snapshot selection manifest

**Files:**

- Modify: `app/core/workflow/entity_evidence_snapshot.py`
- Modify: `app/core/workflow/fact_contract.py`
- Modify: `tests/unit/workflow/test_group_evidence.py`
- Modify: `tests/unit/workflow/test_fact_contract.py`

- [ ] **Step 1: Write failing generic-role and mandatory-selection tests**

```python
def test_direct_strong_warning_event_overrides_legacy_context_role():
    record = canonical_record(
        dimension="kubernetes",
        fact_type="event",
        attribute="event.message",
        value={"type": "Warning", "reason": "Failed", "message": "source failure"},
        directness="direct",
        confidence="high",
        strength="strong",
        metadata={"evidence_role": "context"},
    )
    assert classify_fact_evidence_role(record) == "causal_candidate"


def test_snapshot_manifest_retains_causal_and_one_direct_fact_per_dimension():
    snapshot = build_entity_evidence_snapshot(
        entities=[{"kind": "Pod", "namespace": "demo", "name": "api"}],
        evidence_analysis=evidence_with_many_generic_facts(),
        thinking_events=[],
    )
    manifest = snapshot.to_handoff()["selection_manifest"]
    assert set(manifest["eligible_support_fact_ids"]) <= set(
        manifest["rca_input_fact_ids"]
    )
    assert set(manifest["required_context_fact_ids"]) <= set(
        manifest["rca_input_fact_ids"]
    )
    assert set(manifest["rca_input_fact_ids"]).isdisjoint(
        manifest["omitted_fact_ids"]
    )
```

- [ ] **Step 2: Verify RED**

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_group_evidence.py \
  tests/unit/workflow/test_fact_contract.py -k \
  'warning_event_overrides or snapshot_manifest_retains'
```

Expected: role remains `context` and `selection_manifest` is absent.

- [ ] **Step 3: Implement generic classification and selection**

Add a deterministic `SelectionManifest` containing:

```python
eligible_support_fact_ids: tuple[str, ...]
required_context_fact_ids: tuple[str, ...]
rca_input_fact_ids: tuple[str, ...]
omitted_fact_ids: tuple[str, ...]
omission_reasons: Mapping[str, str]
```

Reconcile roles using only fact type, directness, confidence, strength,
structured severity/reason/status, and typed lifecycle semantics. Do not test
for workload names, Case IDs, expected causes, metric names, or fixture text.

Select all eligible support, at least one strongest direct fact per available
dimension, strong direct configuration context, and negative/contradicting
facts before global fill. If mandatory whole records exceed the budget, raise
`MandatoryEvidenceBudgetError` rather than silently dropping them.

- [ ] **Step 4: Verify GREEN and run the complete Fact suite**

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_group_evidence.py \
  tests/unit/workflow/test_fact_contract.py
```

Expected: PASS.

## Task 3: Make lane identity code-owned

**Files:**

- Modify: `app/core/workflow/fact_contract.py`
- Modify: `app/core/workflow/nodes/root_cause_analyzer.py`
- Modify: `tests/unit/workflow/test_fact_contract.py`
- Modify: `tests/unit/workflow/test_context_handoff.py`

- [ ] **Step 1: Write failing identity-envelope tests**

```python
def test_single_lane_claim_uses_authoritative_entity_not_model_uid():
    ledger = ledger_for("k8s.pod:demo/api:uid-authoritative")
    claim = diagnosed_claim(
        entity_id="k8s.pod:demo/api:uid-mutated",
        supporting_fact_ids=[ledger.records[0].fact_id],
    )
    result = validate_rca_claims(
        claim,
        [ledger],
        authoritative_entity_ids=["k8s.pod:demo/api:uid-authoritative"],
    )
    assert result["diagnostic_status"] == "diagnosed"
    assert result["hypotheses"][0]["entity_id"] == (
        "k8s.pod:demo/api:uid-authoritative"
    )
    assert result["claim_validation"]["model_entity_overrides"] == [{
        "model_entity_id": "k8s.pod:demo/api:uid-mutated",
        "authoritative_entity_id": "k8s.pod:demo/api:uid-authoritative",
    }]


def test_authoritative_lane_still_rejects_foreign_fact():
    result = validate_rca_claims(
        claim_with_foreign_fact(),
        [lane_ledger(), foreign_ledger()],
        authoritative_entity_ids=[lane_ledger().scope_entity_ids[0]],
    )
    assert result["diagnostic_status"] == "inconclusive"
    assert result["claim_validation"]["invalid_fact_ids"]
```

- [ ] **Step 2: Verify RED**

```bash
.venv/bin/python -m pytest -q tests/unit/workflow/test_fact_contract.py \
  -k 'authoritative_entity or foreign_fact'
```

Expected: `validate_rca_claims()` does not accept the new keyword and the
mutated UID is rejected before deterministic ownership is applied.

- [ ] **Step 3: Implement authoritative identity injection**

Extend validation with an optional exact scope:

```python
def validate_rca_claims(
    value,
    ledgers,
    *,
    authoritative_entity_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
```

When there is exactly one authoritative entity, inject it into every
hypothesis before scope validation. Preserve the model-provided value only in
`claim_validation.model_entity_overrides`. Fact membership remains strict; an
unknown or foreign Fact ID still fails closed. Multi-entity contexts retain
the existing explicit/unique-reference validation.

Build the exact authoritative ID from normalized lane ledgers, not Layer text.

- [ ] **Step 4: Verify GREEN**

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_fact_contract.py \
  tests/unit/workflow/test_context_handoff.py
```

Expected: PASS.

## Task 4: Persist formal RCA and add one constrained repair

**Files:**

- Modify: `app/core/workflow/nodes/root_cause_analyzer.py`
- Modify: `app/core/workflow/nodes/base.py`
- Modify: `tests/unit/workflow/test_context_handoff.py`
- Create: `tests/unit/workflow/test_rca_artifacts.py`

- [ ] **Step 1: Write failing output/archive test**

```python
def test_rca_persists_input_model_output_validated_output_and_claim(tmp_path, monkeypatch):
    monkeypatch.setenv("AIOPS_CONTEXT_ARCHIVE_ROOT", str(tmp_path))
    node = configured_rca_node(run_id="run-g1", outputs=[valid_claim()])
    result = node.execute(single_lane_state())
    root = tmp_path / "run-g1"
    assert (root / "node_inputs/rca.input.json").exists()
    assert (root / "node_outputs/rca.attempt-1.model.json").exists()
    assert (root / "node_outputs/rca.output.json").exists()
    assert (root / "node_outputs/claim_validation.output.json").exists()
    assert json.loads((root / "node_outputs/rca.output.json").read_text()) == (
        json.loads(result["rca_analysis"])
    )
```

- [ ] **Step 2: Write failing bounded-repair tests**

```python
def test_rca_repairs_once_when_invalid_output_has_eligible_support():
    node = configured_rca_node(outputs=[invalid_claim(), valid_claim()])
    result = node.execute(single_lane_state_with_eligible_support())
    assert json.loads(result["rca_analysis"])["diagnostic_status"] == "diagnosed"
    assert node.ai_call.call_count == 2


def test_rca_does_not_retry_missing_source_data_or_retry_twice():
    missing = configured_rca_node(outputs=[invalid_claim(), valid_claim()])
    missing.execute(single_lane_state_without_eligible_support())
    assert missing.ai_call.call_count == 1

    twice = configured_rca_node(outputs=[invalid_claim(), invalid_claim(), valid_claim()])
    result = twice.execute(single_lane_state_with_eligible_support())
    assert json.loads(result["rca_analysis"])["diagnostic_status"] == "inconclusive"
    assert twice.ai_call.call_count == 2
```

- [ ] **Step 3: Verify RED**

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_rca_artifacts.py \
  tests/unit/workflow/test_context_handoff.py -k 'rca_repairs_once or retry_twice'
```

Expected: output files are absent and only one model call occurs.

- [ ] **Step 4: Implement output persistence and repair decision**

Add a general `_archive_node_output()` helper. RCA archives each raw structured
model attempt, each validated attempt, selected `rca.output.json`, and separate
claim-validation JSON.

Retry exactly once when:

```python
first_result_is_invalid_or_inconclusive
and snapshot.selection_manifest.eligible_support_fact_ids
and failure_is_not_source_absence
and not cancel_event.is_set()
```

The second call is tool-free and receives only the exact lane identity,
eligible support facts, required context facts, validation reasons, and output
schema. It cannot broaden namespace/Pod scope.

- [ ] **Step 5: Verify GREEN and full RCA tests**

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_rca_artifacts.py \
  tests/unit/workflow/test_context_handoff.py \
  tests/unit/workflow/test_fast_paths.py
```

Expected: PASS.

## Task 5: Persist the strong parallel handoff

**Files:**

- Modify: `app/core/workflow/nodes/parallel_evidence.py`
- Modify: `app/core/workflow/executor.py`
- Modify: `app/core/workflow/state.py`
- Modify: `tests/unit/workflow/test_parallel_evidence.py`
- Modify: `tests/unit/workflow/test_executor_timing.py`

- [ ] **Step 1: Write failing group artifact and executor snapshot tests**

```python
def test_parallel_lane_returns_reloadable_authoritative_artifact(tmp_path, monkeypatch):
    node = configured_parallel_node(tmp_path, monkeypatch)
    result = node.execute(parallel_state(3))
    assert len(result["group_results"]) == 3
    for group in result["group_results"]:
        artifact = group["lane_diagnosis_artifact"]
        assert artifact["contract_version"] == "aiops.lane-diagnosis-artifact.v1"
        LaneDiagnosisArtifactWriter(group["archive_run_id"]).reload_and_verify(artifact)


def test_executor_parallel_snapshot_contains_ordered_reloadable_group_index():
    snapshot = executor()._extract_state_snapshot(
        {"group_results": three_reloadable_group_results()},
        "parallel_evidence",
    )
    assert snapshot["group_count"] == 3
    assert [item["group_id"] for item in snapshot["groups"]] == ["g1", "g2", "g3"]
    assert all(item["artifact_ref"] for item in snapshot["groups"])
```

- [ ] **Step 2: Verify RED**

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_parallel_evidence.py \
  tests/unit/workflow/test_executor_timing.py -k \
  'reloadable_authoritative_artifact or parallel_snapshot_contains'
```

Expected: lane artifact key is absent and executor snapshot is `{}`.

- [ ] **Step 3: Implement ordered lane artifact fan-in**

After snapshot and RCA finish, persist `LaneDiagnosisArtifact`; return its
serialized envelope in `group_results`. Do not copy raw tool output into the
top-level state.

Add the executor `parallel_evidence` projection:

```python
{
    "contract_version": "aiops.parallel-evidence-output.v1",
    "group_count": len(groups),
    "groups": [{
        "group_id": group["group_id"],
        "presentation_index": group["presentation_index"],
        "entities": group["entities"],
        "diagnostic_status": group["diagnostic_status"],
        "artifact_ref": group["lane_diagnosis_artifact_ref"],
        "snapshot_sha256": group["lane_diagnosis_artifact"]["artifact_refs"]["snapshot"]["sha256"],
    } for group in ordered_groups],
}
```

The executor archive output must contain this projection and the reloadable
artifact references. SSE may retain only the compact projection.

- [ ] **Step 4: Verify GREEN**

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_parallel_evidence.py \
  tests/unit/workflow/test_parallel_evidence_stream.py \
  tests/unit/workflow/test_executor_timing.py
```

Expected: PASS.

## Task 6: Fail-closed final rendering and dimension states

**Files:**

- Modify: `app/core/workflow/nodes/conclusion_formatter.py`
- Modify: `app/core/workflow/group_evidence.py`
- Modify: `tests/unit/workflow/test_parallel_evidence.py`
- Modify: `tests/unit/workflow/test_group_evidence.py`
- Modify: `tests/unit/workflow/test_fast_paths.py`

- [ ] **Step 1: Write failing conclusion-authority tests**

```python
def test_single_path_inconclusive_rca_cannot_publish_narrative_diagnosis():
    node = conclusion_node_with_llm("root cause is definitely X, confidence 99%")
    report = node.execute(single_state_with_invalid_formal_rca())["conclusion"]
    assert "diagnostic_status: inconclusive" in report
    assert "confidence 99%" not in report


def test_parallel_report_uses_only_validated_selected_rca():
    report = ConclusionFormatterNode().execute(
        state_with_invalid_group_narrative_and_inconclusive_artifact()
    )["conclusion"]
    assert "证据不足" in report
    assert "unsupported model root" not in authoritative_entity_card(report)
```

- [ ] **Step 2: Write failing empty-state vocabulary test**

```python
@pytest.mark.parametrize("status", [
    "present", "unselected", "not_applicable", "absent", "error", "unknown",
])
def test_dimension_status_round_trips_without_collapsing_to_absent(status):
    report = render_dimension(dimension_summary(status=status))
    assert status in report
```

- [ ] **Step 3: Verify RED**

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_parallel_evidence.py \
  tests/unit/workflow/test_group_evidence.py \
  tests/unit/workflow/test_fast_paths.py -k \
  'inconclusive_rca_cannot or only_validated_selected or status_round_trips'
```

Expected: legacy narrative can override formal RCA and statuses collapse.

- [ ] **Step 4: Implement deterministic authority**

Parse formal RCA before any conclusion model call. If claim validation is not
valid or status is inconclusive, bypass authoritative narrative generation and
render an inconclusive card with real snapshot facts and exact reasons. If it
is diagnosed, entity/root/confidence/support IDs come only from validated RCA.
Optional prose is labelled non-authoritative and cannot replace these fields.

Preserve the six dimension statuses exactly and render query/selection
limitations separately.

- [ ] **Step 5: Verify GREEN**

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_parallel_evidence.py \
  tests/unit/workflow/test_group_evidence.py \
  tests/unit/workflow/test_fast_paths.py
```

Expected: PASS.

## Task 7: Retained-artifact replay and no-special-case gate

**Files:**

- Create: `tests/replay/workflow/test_authoritative_evidence_replay.py`
- Create: `tests/replay/workflow/fixtures/README.md`
- Modify only if a failing replay proves it: files from Tasks 1-6.

- [ ] **Step 1: Write replay tests against copied minimal generic fixtures**

The fixtures contain canonical ledgers and previous malformed RCA candidates,
not namespace/Case behavior in production code.

```python
def test_replay_preserves_decisive_facts_through_selected_rca_and_final():
    replay = replay_fixture("direct-event-configuration-runtime")
    assert replay.snapshot.selection_manifest.eligible_support_fact_ids
    assert replay.selected_rca["claim_validation"]["valid"] is True
    assert set(replay.selected_rca["supporting_fact_ids"]) <= set(
        replay.final_fact_ids
    )


def test_replay_model_uid_mutation_cannot_change_lane_identity():
    replay = replay_fixture("mutated-model-entity")
    assert replay.final_entity_id == replay.authoritative_entity_id
    assert replay.cross_lane_fact_ids == []
```

- [ ] **Step 2: Add a production static-policy gate**

```python
def test_authoritative_policy_contains_no_fixture_specific_branches():
    production = read_policy_sources()
    forbidden = load_fixture_only_identifiers()
    assert not any(identifier in production for identifier in forbidden)
```

The forbidden list contains only test namespace/workload/Case identifiers; it
must not prohibit generic Kubernetes vocabulary or source schemas.

- [ ] **Step 3: Verify RED, then fix only generic contract defects**

```bash
.venv/bin/python -m pytest -q tests/replay/workflow
```

Expected initially: replay exposes missing persistence/authority behavior; after
Tasks 1-6, PASS without adding fixture branches.

- [ ] **Step 4: Run the complete workflow regression suite**

```bash
.venv/bin/python -m pytest -q tests/unit/workflow tests/unit/context \
  tests/replay/workflow
```

Expected: PASS.

## Task 8: Review, build, push, and deploy a fresh frozen version

**Files:**

- Modify: `VERSION`
- Modify image tag fields in the existing deployment path only as required by
  the repository's version workflow.
- Do not modify Case definitions, prompts, or acceptance criteria.

- [ ] **Step 1: Run code quality and full relevant tests**

```bash
.venv/bin/python -m pytest -q tests/unit/workflow tests/unit/context \
  tests/replay/workflow
git diff --check
```

Expected: PASS and no whitespace errors.

- [ ] **Step 2: Perform an independent implementation review**

Review invariants, no-special-case policy, artifact reload, claim authority,
and dirty-worktree preservation. Fix only reviewed defects with a new failing
test first.

- [ ] **Step 3: Increment the Robusta image version once**

Choose the next unused version after `11.0.108`, update only the repository's
normal version/deployment references, and record source hashes.

- [ ] **Step 4: Build, push, delete, and deploy with the normal Make workflow**

```bash
make delete
make build
make push
make deploy
```

Expected: all commands exit 0; deployed image digest matches the pushed digest;
new Robusta Pod UID is Ready with zero restarts; MCPStander remains the frozen
compatible version unless its source changes are required and reviewed.

- [ ] **Step 5: Verify core connectivity**

Expected checks:

- backend health HTTP 200, config loaded, AI initialized;
- frontend HTTP 200;
- 5/5 MCP servers and expected tool count loaded;
- no old Robusta Pod remains serving the endpoint.

## Task 9: New non-overwriting live closure series

**Files:**

- Create a new `agent-loop/` validation workspace and a new
  `reports/live-validation/` run directory.
- Never overwrite the accepted 2026-08-17 frozen series.

- [ ] **Step 1: Freeze version, hashes, prompts, Cases, and rules**

Record image digest, Pod UID, source hash, config hash, Case hash, exact request
contract, and set the new board to frozen before the first diagnosis request.

- [ ] **Step 2: Healthy baseline**

Clean Cases, prove zero Case namespaces, and record backend/frontend/MCP health.

- [ ] **Step 3: Execute one request each for N=1 OOM and N=1 non-OOM**

For each run retain exact wall/node/tool time, full SSE, snapshot artifact,
formal RCA attempts, claim validation, final projection, and independent lane
audit.

- [ ] **Step 4: Execute fixed N=3, N=5, and N=10 runs**

Use the same prompt and `format=sse`, `stream=true`, `max_steps=50`. Validate
every Case independently before the single diagnosis request. Record elapsed
time for comparison but do not fail a correct run only for being slow.

- [ ] **Step 5: Verify every lane chain**

For every lane:

```text
tool source -> canonical ledger -> snapshot -> selection manifest
-> RCA input -> model attempt(s) -> validated RCA -> claim validation
-> deterministic final Fact IDs
```

Every reference and hash must reload. Diagnosed lanes require valid support;
inconclusive lanes must retain exact reasons and real high-value evidence.

- [ ] **Step 6: Independent final review**

The reviewer separately judges measurement integrity, entity isolation,
evidence value, persistence/reload, claim authority, single/multi consistency,
small-model stability, and efficiency. B2 is complete only with `ACCEPT` and no
production Case-specific branch.

