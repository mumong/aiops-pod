# Tasks: 可观测性异常 Case 数据集

**Input**: Design documents from `/specs/007-observability-case-dataset/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/dataset-contract.md, quickstart.md

**Tests**: This feature requires validation tasks because the project constitution requires evidence-first and test-first delivery for behavior-impacting work.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or only reads shared context
- **[Story]**: User story mapping from spec.md
- Every task includes exact target file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the standalone dataset repository and keep the current agent repository limited to contracts/specs.

- [ ] T001 Create standalone dataset repository directory at `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/README.md`
- [ ] T002 Create dataset root manifest at `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/dataset.yaml`
- [ ] T003 [P] Create dataset schema directory at `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/schemas/README.md`
- [ ] T004 [P] Create case template directory at `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/templates/case/README.md`
- [ ] T005 [P] Document data-source boundaries in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/docs/data-sources.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define reusable schemas and validation rules that every case must follow.

**CRITICAL**: No case data should be collected until these files exist, otherwise case formats will drift.

- [ ] T006 Create case metadata schema in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/schemas/case.schema.yaml`
- [ ] T007 [P] Create Prometheus artifact schema in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/schemas/metrics.schema.yaml`
- [ ] T008 [P] Create Elasticsearch/Filebeat log artifact schema in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/schemas/logs.schema.yaml`
- [ ] T009 [P] Create DeepFlow artifact schema in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/schemas/deepflow.schema.yaml`
- [ ] T010 [P] Create Kubernetes snapshot schema in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/schemas/k8s.schema.yaml`
- [ ] T011 Create ground-truth and evaluation schema in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/schemas/evaluation.schema.yaml`
- [ ] T012 Create fixture validation design in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/tools/validate_case.md`
- [ ] T013 Mirror the consumer contract from `specs/007-observability-case-dataset/contracts/dataset-contract.md` to `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/docs/consumer-contract.md`

**Checkpoint**: Schemas and contract are ready; user story work can begin independently.

---

## Phase 3: User Story 1 - 以异常 Case 归档三类可观测证据 (Priority: P1) MVP

**Goal**: Create the first complete case template and TerminatingStuck finalizer sample using Prometheus, Elasticsearch/Filebeat, DeepFlow, and K8s evidence.

**Independent Test**: A reviewer can inspect only `cases/pod-terminating-finalizer-stuck-001/` and understand the incident window, telemetry coverage, root cause, and remediation expectation without querying the live cluster.

### Tests for User Story 1

- [ ] T014 [P] [US1] Add case fixture validation checklist in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/tests/fixtures/pod-terminating-finalizer-stuck-001.checklist.md`
- [ ] T015 [P] [US1] Add leakage test checklist to ensure diagnosis inputs exclude labels and expected files in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/tests/contracts/no-ground-truth-leakage.md`

### Implementation for User Story 1

- [ ] T016 [US1] Create case metadata in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/cases/pod-terminating-finalizer-stuck-001/case.yaml`
- [ ] T017 [P] [US1] Create topology description in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/cases/pod-terminating-finalizer-stuck-001/topology.yaml`
- [ ] T018 [P] [US1] Create Prometheus query definitions in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/cases/pod-terminating-finalizer-stuck-001/metrics/prometheus_queries.yaml`
- [ ] T019 [P] [US1] Create Elasticsearch/Filebeat query definitions in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/cases/pod-terminating-finalizer-stuck-001/logs/elasticsearch_queries.yaml`
- [ ] T020 [P] [US1] Create DeepFlow query definitions in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/cases/pod-terminating-finalizer-stuck-001/traces/deepflow_queries.yaml`
- [ ] T021 [US1] Capture Kubernetes Pod snapshot in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/cases/pod-terminating-finalizer-stuck-001/k8s/pod.yaml`
- [ ] T022 [US1] Capture Kubernetes describe output in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/cases/pod-terminating-finalizer-stuck-001/k8s/describe.txt`
- [ ] T023 [US1] Capture Kubernetes event stream in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/cases/pod-terminating-finalizer-stuck-001/k8s/events.jsonl`
- [ ] T024 [US1] Capture Prometheus range results in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/cases/pod-terminating-finalizer-stuck-001/metrics/prometheus_range.jsonl`
- [ ] T025 [US1] Capture Elasticsearch/Filebeat logs in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/cases/pod-terminating-finalizer-stuck-001/logs/logs.jsonl`
- [ ] T026 [US1] Capture DeepFlow flow results in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/cases/pod-terminating-finalizer-stuck-001/traces/deepflow_flows.jsonl`
- [ ] T027 [US1] Capture DeepFlow span results or explicit weak-signal marker in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/cases/pod-terminating-finalizer-stuck-001/traces/deepflow_spans.jsonl`
- [ ] T028 [US1] Create ground-truth labels in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/cases/pod-terminating-finalizer-stuck-001/labels.yaml`
- [ ] T029 [US1] Create expected root cause in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/cases/pod-terminating-finalizer-stuck-001/expected/root_cause.json`
- [ ] T030 [US1] Create safe remediation expectation in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/cases/pod-terminating-finalizer-stuck-001/expected/remediation.json`
- [ ] T031 [US1] Create evaluation rubric in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/cases/pod-terminating-finalizer-stuck-001/evaluation/rubric.yaml`

**Checkpoint**: First case is independently reviewable and demonstrates the complete dataset shape.

---

## Phase 4: User Story 2 - 为 Agent 诊断提供标准消费契约 (Priority: P2)

**Goal**: Define how the future agent reads case data without reading ground truth, and how the evaluator reads expected labels.

**Independent Test**: A contract review can identify diagnosis input files and evaluation-only files for any case.

### Tests for User Story 2

- [ ] T032 [P] [US2] Add diagnosis-input contract example in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/tests/contracts/diagnosis-input-contract.md`
- [ ] T033 [P] [US2] Add evaluator-only contract example in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/tests/contracts/evaluation-only-contract.md`

### Implementation for User Story 2

- [ ] T034 [US2] Create diagnosis input manifest format in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/schemas/diagnosis-input.schema.yaml`
- [ ] T035 [US2] Create evaluator result format in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/schemas/evaluator-result.schema.yaml`
- [ ] T036 [US2] Document agent offline consumption flow in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/docs/offline-agent-consumption.md`
- [ ] T037 [US2] Document scorer flow and anti-leakage boundary in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/docs/evaluation-flow.md`
- [ ] T038 [US2] Add a sample diagnosis-input manifest for the TerminatingStuck case in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/cases/pod-terminating-finalizer-stuck-001/diagnosis-input.yaml`

**Checkpoint**: Future agent and scorer responsibilities are separated before runtime integration work begins.

---

## Phase 5: User Story 3 - 支持逐步扩展多个异常类型 (Priority: P3)

**Goal**: Make it easy to add additional Pod abnormal cases from existing e2e manifests without changing the dataset structure.

**Independent Test**: At least three additional case stubs can be created from existing manifests using the same schema.

### Tests for User Story 3

- [ ] T039 [P] [US3] Add multi-case schema consistency checklist in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/tests/contracts/multi-case-consistency.md`

### Implementation for User Story 3

- [ ] T040 [US3] Create ImagePullFailed case stub in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/cases/pod-imagepull-invalid-registry-001/case.yaml`
- [ ] T041 [US3] Create OOMKilled case stub in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/cases/pod-oomkilled-memory-limit-001/case.yaml`
- [ ] T042 [US3] Create VolumeMountFailed case stub in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/cases/pod-volumemount-missing-configmap-001/case.yaml`
- [ ] T043 [US3] Document mapping from existing e2e manifests to dataset abnormal types in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/docs/e2e-manifest-case-mapping.md`
- [ ] T044 [US3] Update root case index in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/dataset.yaml`

**Checkpoint**: Dataset schema supports expansion beyond the first case.

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Documentation quality, safety review, and handoff readiness.

- [ ] T045 [P] Review DeepFlow evidence wording in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/docs/data-sources.md` to avoid overstating weak trace signals
- [ ] T046 [P] Review remediation safety expectations in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/cases/pod-terminating-finalizer-stuck-001/expected/remediation.json`
- [ ] T047 [P] Add dataset contribution guide in `/root/huhu/agent/combine-aiops-mcp/aiops-observability-dataset/CONTRIBUTING.md`
- [ ] T048 Validate quickstart steps against `specs/007-observability-case-dataset/quickstart.md`
- [ ] T049 Push the final dataset-spec and task commits to the agreed remote branch from `/root/huhu/agent/combine-aiops-mcp/robusta`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational and is the MVP.
- **User Story 2 (Phase 4)**: Depends on Foundational; can run after or alongside US1 once schemas are stable.
- **User Story 3 (Phase 5)**: Depends on Foundational and benefits from US1 as a worked example.
- **Final Phase**: Depends on the selected user stories being complete.

### User Story Dependencies

- **US1**: No dependency on US2 or US3 after foundational schemas are ready.
- **US2**: No dependency on US3; may reference US1 sample case for examples.
- **US3**: No dependency on US2; should reuse the same schemas and template from US1.

### Parallel Opportunities

- T003, T004, and T005 can run in parallel.
- T007, T008, T009, and T010 can run in parallel after T006 starts.
- T018, T019, and T020 can run in parallel.
- T024, T025, T026, and T027 can run in parallel after query definitions are ready and data windows are fixed.
- T032 and T033 can run in parallel.
- T040, T041, and T042 can run in parallel.

---

## Parallel Example: User Story 1

```bash
# Parallel documentation/schema work for the first case:
Task: "Create Prometheus query definitions in .../metrics/prometheus_queries.yaml"
Task: "Create Elasticsearch/Filebeat query definitions in .../logs/elasticsearch_queries.yaml"
Task: "Create DeepFlow query definitions in .../traces/deepflow_queries.yaml"

# Parallel telemetry result capture after the time window is fixed:
Task: "Capture Prometheus range results in .../metrics/prometheus_range.jsonl"
Task: "Capture Elasticsearch/Filebeat logs in .../logs/logs.jsonl"
Task: "Capture DeepFlow flow results in .../traces/deepflow_flows.jsonl"
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1.
2. Complete Phase 2.
3. Complete Phase 3 for `pod-terminating-finalizer-stuck-001`.
4. Stop and validate that the first case can be understood offline and does not leak ground truth into diagnosis inputs.

### Incremental Delivery

1. Deliver one high-quality TerminatingStuck finalizer case.
2. Add the agent/scorer consumption contract.
3. Add additional case stubs from existing e2e manifests.
4. Only after the data contract stabilizes, consider current agent runtime integration.

### Out of Scope For This Task List

- Modifying current `/ask` or `/query` runtime behavior.
- Building a full web UI for dataset browsing.
- Replacing Prometheus, Elasticsearch/Filebeat, or DeepFlow.
- Treating Grafana screenshots as sufficient dataset evidence without query definitions and raw/normalized results.
