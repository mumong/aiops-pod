# Authoritative Entity Evidence Snapshot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the multi-anomaly path use one authoritative per-Pod Fact Ledger projection for collection handoff, RCA validation, and deterministic final reporting, then prove the result with a frozen-image live N=1/N=3/N=5/N=10 test series.

**Architecture:** Build `EntityEvidenceSnapshot` as an index over the existing `FactLedger`/`FactRecord` contract, never as a competing fact schema. Split multi-entity issue groups into atomic Pod diagnostic lanes, derive report cards from the same snapshot that formal RCA consumes, and keep `thinking_events` only for coverage, limitations, streaming, and raw archive drill-down. Extend generic Kubernetes and Tempo adapters only where source facts are currently lost or their coverage semantics are false.

**Tech Stack:** Python 3, Pydantic, pytest, LangGraph workflow nodes, Kubernetes, Docker/registry Make targets, Robusta AIOps backend, MCPStander observability server.

---

### Task 1: Lock the duplicate-registry bug with replay-style unit tests

**Files:**
- Modify: `tests/unit/workflow/test_group_evidence.py`
- Modify: `tests/unit/workflow/test_parallel_evidence.py`

- [ ] Add a test whose `evidence_analysis.tool_data.fact_ledger` contains a canonical Kubernetes `fact_id`, while its audit `thinking_event` contains the same source observation without a ledger.
- [ ] Assert that the final `dimension_evidence_by_entity` contains exactly the canonical ID and does not mint a `fact-k8s-*` replacement.
- [ ] Add a formal-RCA test asserting that a valid supporting ID survives `_attach_validated_diagnosis()` and remains attached to the correct Pod.
- [ ] Run the focused tests and verify RED because the current report projection is built from `thinking_events`.

Run:

```bash
pytest -q tests/unit/workflow/test_group_evidence.py tests/unit/workflow/test_parallel_evidence.py
```

Expected RED: canonical Kubernetes ID is absent from the report-side registry or the entity is downgraded to `inconclusive`.

### Task 2: Introduce one authoritative `EntityEvidenceSnapshot`

**Files:**
- Create: `app/core/workflow/entity_evidence_snapshot.py`
- Modify: `app/core/workflow/nodes/parallel_evidence.py`
- Modify: `app/core/workflow/group_evidence.py`
- Test: `tests/unit/workflow/test_group_evidence.py`
- Test: `tests/unit/workflow/test_parallel_evidence.py`

- [ ] Define a frozen snapshot projection containing entity identities, normalized ledgers, `fact_id -> FactRecord`, facts grouped by entity/dimension, dimension coverage, limitations, and archive references.
- [ ] Build authoritative facts only with `extract_fact_ledgers_from_evidence_analysis()`; preserve complete `FactRecord.model_dump()` data and unknown metadata.
- [ ] Use final semantic `thinking_events` only to supplement query counts, empty/error coverage, limitations, and archive references. Do not create Fact IDs from those events.
- [ ] Replace `_build_group_result()` report aggregation with the snapshot projection and retain a serialized snapshot handoff in each group result.
- [ ] Resolve `_attach_validated_diagnosis()` supporting and contradicting IDs against the same snapshot index.
- [ ] Run focused tests and verify GREEN.

Acceptance checks:

```text
RCA input fact_id == validation fact_id == final card fact_id
thinking event without canonical ledger contributes no new diagnostic fact
all four dimensions remain present as honest present/empty/absent/error coverage objects
```

### Task 3: Preserve generic Kubernetes causal observations

**Files:**
- Modify: `app/core/workflow/fact_contract.py`
- Test: `tests/unit/workflow/test_fact_contract.py`
- Test: `tests/unit/workflow/test_group_evidence.py`

- [ ] Add RED tests for Pod conditions, current waiting reason/message, current and previous terminated reason/message/exit code, Kubernetes Events, and configuration references.
- [ ] Add a RED test proving internal parser/summarizer states and table headers never become facts.
- [ ] Extend `build_kubernetes_lifecycle_fact_ledger()` with generic source-path extraction for those fields, stable source-derived IDs, bounded values, evidence refs, and metadata carrying `diagnostic_role` plus source path.
- [ ] Classify warning/waiting/event messages as `causal_candidate`, lifecycle state/exit/restarts as `symptom`, topology/configuration as `context`, and zero-valued categorical observations as `negative_observation`.
- [ ] Do not encode case IDs, workload names, expected causes, or remediation labels.
- [ ] Run focused tests and verify GREEN.

### Task 4: Make every Pod an atomic diagnostic lane

**Files:**
- Modify: `app/core/workflow/nodes/parallel_evidence.py`
- Test: `tests/unit/workflow/test_parallel_evidence.py`

- [ ] Add a RED test with two Pods in one coarse Layer issue group and assert two independent EvidenceCollector/RCA executions.
- [ ] Expand parent issue groups to stable child lanes before executor submission, preserving `parent_group_id`, presentation order, status keywords, and one Pod per scoped handoff.
- [ ] Ensure one failed lane returns an explicit limitation without cancelling sibling lanes.
- [ ] Validate each entity RCA only against its lane snapshot; never clear a sibling diagnosis because another Pod lacks evidence.
- [ ] Fan lanes back into deterministic group results without merging their Fact registries.
- [ ] Run the focused tests and verify GREEN.

### Task 5: Rank and render source value without misleading evidence

**Files:**
- Modify: `app/core/workflow/group_evidence.py`
- Modify: `app/core/workflow/nodes/conclusion_formatter.py`
- Test: `tests/unit/workflow/test_group_evidence.py`
- Test: `tests/unit/workflow/test_parallel_evidence.py`

- [ ] Add RED tests that RCA supporting facts render before direct causal candidates, symptoms, negative observations, and context.
- [ ] Add a RED test that `reason=NodeLost,value=0` is shown only as a negative/exclusion observation, never as a positive anomaly or root cause.
- [ ] Preserve metric name, value, unit, trend, purpose, identity labels, source reference, and timestamps in expandable detail.
- [ ] Render restart count as persistence/symptom evidence unless formal RCA cites it alongside a causal source fact.
- [ ] Keep deterministic per-Pod four-dimensional cards independent of narrative LLM length.
- [ ] Run focused tests and verify GREEN.

### Task 6: Correct Tempo coverage and correlation semantics in MCPStander

**Files:**
- Modify: `../mcpstander/servers/aiops_observability/collectors/tempo.py`
- Modify: `../mcpstander/servers/aiops_observability/query/tracing.py`
- Modify: `../mcpstander/servers/aiops_observability/query/fact_ledger.py`
- Test: `../mcpstander/tests/test_aiops_observability_collectors.py`
- Test: `../mcpstander/tests/test_aiops_observability_query_tracing.py`
- Test: `../mcpstander/tests/test_aiops_observability_query_fact_ledger.py`

- [ ] Add RED tests proving a successful Tempo HTTP lookup with zero parsed spans is `empty`, not `present`.
- [ ] Add RED tests proving parsed spans become tracing FactRecords with complete trace/span identity and source refs.
- [ ] Add RED tests proving only exact normalized trace ID equality is `correlated`; same Pod/path/time without equality is `related_context`.
- [ ] Implement the minimal collector/query/ledger changes and verify the focused MCPStander tests GREEN.

### Task 7: Run automated regression gates

**Files:**
- No production changes during this task.

- [ ] Run Robusta focused workflow/fact tests.
- [ ] Run the complete Robusta unit suite.
- [ ] Run MCPStander focused observability tests and its complete unit suite supported by the repository.
- [ ] Run formatting/lint/type checks exposed by each Makefile.
- [ ] Record command, exit code, duration, passed/failed/skipped counts, and any environment-only limitations in the final live-test audit.

No live image is built until every required local gate is green.

### Task 8: Freeze versions, build, push, and deploy real images

**Files:**
- Modify: `VERSION`
- Modify only if required by the existing deployment contract: `deploy/k8s-simple.yaml`
- Modify MCPStander version/deployment files only if Task 6 changes that component.

- [ ] Capture the pre-deploy Deployments, images, Pod UIDs, health endpoints, and service endpoints.
- [ ] Increment Robusta from `11.0.107` to the next unused version and keep manifest image tags synchronized through the existing Makefile flow.
- [ ] Increment and deploy MCPStander only if its production code changed.
- [ ] Execute exactly the user-authorized deployment flow from the current repositories:

```bash
make delete
make build
make push
make deploy
```

- [ ] Wait on Kubernetes conditions rather than fixed sleeps; verify image digests/tags and new Pod UIDs prove the new code is running.
- [ ] Verify backend `/health`, MCP manager/MCPStander tool connectivity, and frontend service reachability before anomaly testing.

### Task 9: Execute the frozen-code real test matrix

**Files:**
- Create: `reports/live-validation/2026-08-17-authoritative-snapshot/README.md`
- Create one machine-readable and one human-readable audit artifact per run under that directory.

- [ ] Record a healthy baseline backend API run.
- [ ] Deploy and validate N=1 c08 OOM; run diagnosis through the backend API and record Run ID plus exact wall time.
- [ ] Select one non-OOM case deterministically from the available cases, record the selection, deploy/validate/diagnose it, and record Run ID plus exact wall time.
- [ ] Clean anomaly namespaces, then deploy/validate/diagnose fixed N=3, N=5, and N=10 sets in increasing order.
- [ ] Do not modify source, configuration, image, prompt, or test criteria between the first and last matrix run.
- [ ] For every Run ID inspect main and per-lane archives, final report, backend logs, and tool structured results.

Per-run acceptance table:

```text
run_id | cases | start/end/wall time | Pod lanes | tool requested/executed/failed
entity | K8s/Metrics/Logging/Tracing coverage | diagnosed/inconclusive
supporting IDs present in snapshot and report | invalid IDs | value review
```

Explicit value review rejects table headers as facts, zero-valued reason series as positive anomalies, restart-only generic evidence as a complete root cause, missing namespace/Pod binding, Tempo-without-span `present`, and trace correlation without exact ID equality.

### Task 10: Close the loop with a deployment and evidence audit

**Files:**
- Complete: `reports/live-validation/2026-08-17-authoritative-snapshot/README.md`

- [ ] Compare each expected anomaly to source-backed Kubernetes, Metrics, Logging, and Tracing evidence without using case labels as inference inputs.
- [ ] State separately whether evidence was collected, preserved in the snapshot, accepted by RCA, and displayed in the final report.
- [ ] Report exact image versions/digests, deployed Pod UIDs, health results, per-run timings, Run IDs, diagnosed/inconclusive counts, and known limitations.
- [ ] If the frozen series reveals a defect, finish and preserve the entire series before proposing the next code change; do not silently patch between runs.
- [ ] Re-run the final verification commands immediately before claiming completion.

