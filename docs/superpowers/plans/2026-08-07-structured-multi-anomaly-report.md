# Structured Multi-Anomaly Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace truncated free-text multi-group handoff with validated per-entity diagnosis and deterministic Kubernetes/Metrics/Logging/Tracing aggregation, then render a readable multi-anomaly report.

**Architecture:** Add focused Pydantic output models and a pure `group_evidence` aggregation module. `ParallelEvidenceNode` performs one no-tool structured extraction per group after evidence collection, validates entity/fact coverage, and stores structured results. `ConclusionFormatterNode` gives the LLM only the compact structured diagnosis while code renders every entity's four-dimensional evidence matrix and a folded raw appendix.

**Tech Stack:** Python 3.12, Pydantic v2, LangGraph workflow state, pytest, existing AICall structured-output runtime.

---

### Task 1: Define the structured diagnosis contract

**Files:**
- Modify: `app/core/workflow/schemas.py`
- Modify: `app/core/workflow/state.py`
- Test: `tests/unit/workflow/test_structured_schemas.py`

- [ ] **Step 1: Write failing schema tests**

Add tests that validate an `EntityDiagnosisSummary` containing `namespace`, `name`, `status`, `phenomenon`, `root_cause`, `causal_chain`, confidence, supporting/contradicting fact IDs and unknowns, plus a `GroupDiagnosisSummaryOutput` list. Assert confidence is bounded and entity names cannot be empty.

- [ ] **Step 2: Run the schema tests and verify failure**

Run:

```bash
PYTHONPATH=. .venv/bin/pytest -q tests/unit/workflow/test_structured_schemas.py -k group_diagnosis
```

Expected: collection/import failure because the new schemas do not exist.

- [ ] **Step 3: Add the models**

Implement:

```python
class EntityDiagnosisSummary(BaseModel):
    namespace: str = Field(min_length=1)
    name: str = Field(min_length=1)
    status: str = ""
    phenomenon: str = ""
    root_cause: str = "证据不足"
    causal_chain: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    supporting_fact_ids: list[str] = Field(default_factory=list)
    contradicting_fact_ids: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)

class GroupDiagnosisSummaryOutput(BaseModel):
    entities: list[EntityDiagnosisSummary] = Field(default_factory=list)
```

Add a typed `structured_group_diagnosis` field to `WorkflowState` without changing existing fields.

- [ ] **Step 4: Run the schema tests**

Expected: new schema tests pass.

### Task 2: Aggregate evidence by entity and dimension

**Files:**
- Create: `app/core/workflow/group_evidence.py`
- Test: `tests/unit/workflow/test_group_evidence.py`

- [ ] **Step 1: Write failing aggregation tests**

Cover these fixtures:

```python
events = [
    observability_event("query_pod_logs", "logging", "present", facts=[dependency_503]),
    observability_event("query_pod_logs", "logging", "empty", facts=[]),
]
```

Assert:

- each entity always has `kubernetes`, `metrics`, `logging`, `tracing`;
- present followed by empty remains `present`;
- query counters record both calls;
- facts retain `fact_id`, source, value and evidence refs;
- a Pending/no-IP entity marks Logging and Tracing `not_applicable` without invented facts;
- merged entities do not share facts.

- [ ] **Step 2: Run the new tests and verify failure**

Run:

```bash
PYTHONPATH=. .venv/bin/pytest -q tests/unit/workflow/test_group_evidence.py
```

Expected: import failure because `group_evidence.py` does not exist.

- [ ] **Step 3: Implement the pure aggregator**

Provide:

```python
REQUIRED_DIMENSIONS = ("kubernetes", "metrics", "logging", "tracing")

def aggregate_group_evidence(
    entities: list[dict[str, Any]],
    events: list[dict[str, Any]],
    status_keywords: list[str] | None = None,
) -> dict[str, dict[str, dict[str, Any]]]:
    ...
```

Match targets from `structured.entity` first and tool arguments second. For observability facts, prefer canonical `fact_ledger.records`, fall back to `structured.facts`, and deduplicate by fact ID/evidence ref. Aggregate status with `present > weak/partial > empty/absent > error`; convert empty Logging/Tracing to `not_applicable` only when lifecycle evidence proves the container cannot run or the Pod has no IP. Extract compact Kubernetes facts from structured `selected_events`, `key_events`, status/reason/exit/restart fields and readable result summaries.

- [ ] **Step 4: Run aggregation tests**

Expected: all new aggregation tests pass.

### Task 3: Produce validated per-entity diagnosis in ParallelEvidence

**Files:**
- Modify: `app/core/prompts.py`
- Modify: `app/core/workflow/nodes/parallel_evidence.py`
- Test: `tests/unit/workflow/test_parallel_evidence.py`

- [ ] **Step 1: Write failing parallel tests**

Add a fake `call_structured` provider. Feed two entities with distinct facts (c06 exit 2 and c10 liveness HTTP 500/exit 137). Assert each entity receives only its own fact IDs/root cause. Add a legacy event where `content` is 500 characters and `full_content` contains c09's `dependency unavailable -> 503`; assert fallback prefers `full_content`. Assert `dimension_evidence_by_entity` exists and contains all four dimensions.

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
PYTHONPATH=. .venv/bin/pytest -q tests/unit/workflow/test_parallel_evidence.py
```

Expected: assertions fail because current results expose only `summary`.

- [ ] **Step 3: Add the structured prompt**

Define `GROUP_EVIDENCE_SUMMARY_PROMPT` requiring exactly one item per supplied entity, no cross-entity fact reuse, fact-ID-backed conclusions, and `证据不足` for unsupported claims.

- [ ] **Step 4: Implement structured extraction and validation**

After each collector finishes:

1. aggregate events using `aggregate_group_evidence`;
2. serialize only compact per-entity facts into one no-tool `GroupDiagnosisSummaryOutput` call;
3. discard unknown entities and unknown fact IDs;
4. add deterministic `证据不足` entries for missing entities;
5. store `entity_summaries`, `dimension_evidence_by_entity`, archive ID and compatibility summary;
6. use `full_content` before `content` only on the legacy fallback path and mark `legacy_text_fallback`.

- [ ] **Step 5: Run parallel tests**

Expected: all parallel workflow tests pass, including existing archive/isolation tests.

### Task 4: Render readable four-dimensional multi-group reports

**Files:**
- Modify: `app/core/workflow/nodes/conclusion_formatter.py`
- Modify: `app/core/prompts.py`
- Test: `tests/unit/workflow/test_parallel_evidence.py`
- Test: `tests/unit/workflow/test_conclusion_formatter.py`

- [ ] **Step 1: Write failing report tests**

Assert the generated report contains, for every entity:

```markdown
## 异常组 g7 · aiops-case-09/workload
| Kubernetes | present |
| Metrics | present |
| Logging | present |
| Tracing | present |
```

Assert c09 includes `dependency unavailable`, HTTP 503 and trace ID. Assert a later empty query is shown as a limitation but does not change Logging from present. Assert raw per-tool evidence is inside `<details>` and every archive reference remains present.

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
PYTHONPATH=. .venv/bin/pytest -q tests/unit/workflow/test_parallel_evidence.py tests/unit/workflow/test_conclusion_formatter.py
```

Expected: report-layout assertions fail with the old tool-by-tool appendix.

- [ ] **Step 3: Change the LLM input**

Build the multi-group prompt from validated `entity_summaries` plus compact dimension status/facts. Keep one Conclusion LLM call and tell it not to reproduce raw evidence tables.

- [ ] **Step 4: Add deterministic report cards**

Render one entity section per group with status/root cause/logic, then a four-row evidence matrix. Use human labels and representative facts. Render missing dimensions honestly and collect limitations below the table. Move `_build_tool_data_section(events)` into a `<details><summary>逐工具原始证据</summary>` appendix and retain the archive link.

- [ ] **Step 5: Run report tests**

Expected: parallel and conclusion tests pass.

### Task 5: Regression, real-output validation and deployment handoff

**Files:**
- Modify only if a failing regression proves a scoped defect.
- Test: `tests/unit/workflow/test_context_handoff.py`
- Test: `tests/unit/workflow/test_parallel_evidence.py`
- Test: `tests/unit/workflow/test_conclusion_formatter.py`

- [ ] **Step 1: Run focused regression tests**

```bash
PYTHONPATH=. .venv/bin/pytest -q \
  tests/unit/workflow/test_structured_schemas.py \
  tests/unit/workflow/test_group_evidence.py \
  tests/unit/workflow/test_parallel_evidence.py \
  tests/unit/workflow/test_conclusion_formatter.py \
  tests/unit/workflow/test_context_handoff.py
```

Expected: zero failures; normal `<=2` handoff still excludes large `llm_analysis`.

- [ ] **Step 2: Run the complete unit suite**

```bash
PYTHONPATH=. .venv/bin/pytest -q tests/unit
```

Expected: zero failures.

- [ ] **Step 3: Build and deploy the verified AIOps image using repository commands**

Resolve the current Makefile/README deployment target, build an immutable image tag, apply the matching manifests and verify the running image digest and `/health` endpoint. Do not include `deploy/secrets/core.yaml` in commits or overwrite it.

- [ ] **Step 4: Run one real multi-anomaly diagnosis**

Deploy runtime Cases c06, c09 and c10 plus two control-plane Cases. Wait for telemetry according to `test/pod-anomaly-cases/README.md`, invoke one diagnosis, and verify:

- c06 shows runtime exit/HTTP 500 without unsupported configuration claims;
- c09 shows dependency unavailable -> HTTP 503 -> Ready=False;
- c10 shows liveness HTTP 500/restart and does not claim OOMKilled;
- every entity has Kubernetes, Metrics, Logging and Tracing rows;
- present facts are not overwritten by later empty searches.

- [ ] **Step 5: Leave five requested anomalies deployed**

After validation, leave exactly five Case namespaces deployed for user testing and report their IDs, namespaces, current gates and cleanup command. Do not clean them until the user asks.

- [ ] **Step 6: Commit implementation**

Stage only intended source/tests/docs, verify with `git diff --cached --check`, and commit with a scoped feature message. Preserve unrelated user changes.
