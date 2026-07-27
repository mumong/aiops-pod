# Autonomous Observability Query Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 Robusta 的 Qwen Evidence 节点使用 Kubernetes 工具与三个通用
可观测性 MCP 工具，自主组合真实 Metrics、Logging、Tracing 查询，并把有界原始
事实用于 RCA。

**Architecture:** `mcpstander` 新增独立 8100 query server，模型传入 PromQL 或
结构化日志/链路条件，MCP 校验后查询真实数据源并返回统一 observation contract。
`robusta` 保留四节点工作流，只切换 MCP 开关、Evidence 查询指导、Runbook 和
ObservationProcessor；现有 coarse/fine 路径保留为默认关闭的兼容模式。

**Tech Stack:** Python 3.10、MCP 1.12.2、Prometheus HTTP API、Elasticsearch、
DeepFlow ClickHouse、Tempo、pytest、Kubernetes SSE deployment

---

## File Map

### mcpstander

- `servers/aiops_observability/query/common.py`: 实体解析、时间窗、预算、统一结果和
  evidence ref。
- `servers/aiops_observability/query/metrics.py`: PromQL scope 校验、执行、series
  去重和样本裁剪。
- `servers/aiops_observability/query/logs.py`: 结构化条件转 ES DSL、UID 优先查询、
  日志去重。
- `servers/aiops_observability/query/tracing.py`: 结构化条件转 ClickHouse SQL、
  DeepFlow flow 与 Tempo span 关联。
- `servers/holmes_tools/aiops_observability_query.py`: MCP Tool schema 与 handler。
- `servers/aiops_observability_query_server.py`: stdio MCP server entry；由现有
  `mcp-proxy --server sse` 包装后对外提供 8100/SSE。
- `tests/test_aiops_observability_query_*.py`: 模块组测试。
- `deploy/*.yaml`, `Dockerfile`: 8100 server 配置。

### robusta

- `app/core/prompts.py`: 从 mandatory coarse 改为 autonomous query loop。
- `app/core/context/observation.py`: 解析 generic query contract，保留真实 facts。
- `app/core/workflow/nodes/evidence_collector.py`: 通用工具指导、细节补证与统计适配。
- `deploy/configmap/config.yaml`: autonomous/coarse/fine 开关。
- `deploy/configmap/runbooks.yaml`: 三个首批场景的查询知识与证据边界。
- `tests/unit/aicall/test_observation_processing.py`: observation contract 测试。
- `tests/unit/workflow/test_evidence_dynamic_stop.py`: Evidence 行为测试。

## Task 1: MCP Contract And Shared Primitives

**Files:**

- Create: `/root/huhu/agent/combine-aiops-mcp/mcpstander/tests/test_aiops_observability_query_contract.py`
- Create: `/root/huhu/agent/combine-aiops-mcp/mcpstander/servers/aiops_observability/query/__init__.py`
- Create: `/root/huhu/agent/combine-aiops-mcp/mcpstander/servers/aiops_observability/query/common.py`
- Create: `/root/huhu/agent/combine-aiops-mcp/mcpstander/servers/holmes_tools/aiops_observability_query.py`

- [ ] **Step 1: Write the failing contract test group**

Test that:

```python
assert [tool.name for tool in TOOLS] == [
    "execute_pod_promql",
    "query_pod_logs",
    "query_pod_tracing",
]
assert all("scenario" not in tool.inputSchema["properties"] for tool in TOOLS)
assert all("purpose" in tool.inputSchema["required"] for tool in TOOLS)
```

Also assert common result bounding preserves `facts`, `samples`, `query`, `coverage` and
`evidence_refs` while serialized UTF-8 size is at most 6144 bytes.
For every rejected query, assert `ok=false`、`status=query_rejected`、
`coverage=error` and stable `error.code/error.message`.

- [ ] **Step 2: Run the contract test group and verify RED**

```bash
cd /root/huhu/agent/combine-aiops-mcp/mcpstander
pytest -q tests/test_aiops_observability_query_contract.py
```

Expected: FAIL because the query package and tools do not exist.

- [ ] **Step 3: Implement shared contract**

Implement:

```python
MAX_RESULT_BYTES = 6144
MAX_WINDOW_SECONDS = 7200

def resolve_pod_scope(namespace: str, pod: str, pod_uid: str | None) -> dict:
    ...

def parse_bounded_window(arguments: dict) -> tuple[str, str]:
    ...

def evidence_ref(dimension: str, namespace: str, pod: str, payload: object) -> str:
    ...

def bound_result(payload: dict, max_bytes: int = MAX_RESULT_BYTES) -> dict:
    ...
```

`bound_result` only removes tail samples/facts and marks `truncated=true`; it must never
remove `entity`、`purpose`、`coverage`、`query` or all evidence facts.

- [ ] **Step 4: Register the three tool schemas**

Use the exact contract in
`/root/huhu/agent/combine-aiops-mcp/data/specs/003-autonomous-observability-query/contracts/mcp-tools.yaml`.
Descriptions must explain that the model selects queries and MCP does not route by fault type.

- [ ] **Step 5: Run the contract group and verify GREEN**

```bash
pytest -q tests/test_aiops_observability_query_contract.py
```

Expected: PASS.

## Task 2: Generic Metrics Query

**Files:**

- Create: `/root/huhu/agent/combine-aiops-mcp/mcpstander/tests/test_aiops_observability_query_metrics.py`
- Create: `/root/huhu/agent/combine-aiops-mcp/mcpstander/servers/aiops_observability/query/metrics.py`
- Modify: `/root/huhu/agent/combine-aiops-mcp/mcpstander/servers/holmes_tools/aiops_observability_query.py`

- [ ] **Step 1: Write the failing Metrics test group**

Cover:

```python
def test_rejects_unscoped_selector(): ...
def test_rejects_one_scoped_selector_plus_unscoped_selector(): ...
def test_accepts_multiple_exact_pod_selectors_for_usage_divided_by_limit(): ...
def test_rejects_range_over_two_hours(): ...
def test_deduplicates_scrapers_without_summing_values(): ...
def test_keeps_real_first_peak_last_samples_and_query(): ...
```

The important negative query is:

```promql
container_memory_working_set_bytes{namespace="ns",pod="p"} or up
```

It must be rejected because `up` is an unscoped vector selector.

- [ ] **Step 2: Run Metrics tests and verify RED**

```bash
pytest -q tests/test_aiops_observability_query_metrics.py
```

- [ ] **Step 3: Implement conservative PromQL validation**

Requirements:

- query length <= 2000。
- parse every vector selector and require exact namespace and pod matchers。
- reject regex or negative matchers for namespace/pod。
- allow scalar literals/functions and multiple fully scoped selectors。
- instant uses `/api/v1/query`; range uses `/api/v1/query_range`。

- [ ] **Step 4: Implement deterministic result compaction**

Logical series key excludes scraper labels:

```python
SCRAPER_LABELS = {
    "job", "instance", "endpoint", "service",
    "prometheus", "prometheus_replica",
}
```

Do not sum duplicates. Keep one logical series, 20 evenly spaced samples, and facts for current
or peak values.

- [ ] **Step 5: Run Metrics and contract tests**

```bash
pytest -q \
  tests/test_aiops_observability_query_contract.py \
  tests/test_aiops_observability_query_metrics.py
```

## Task 3: Generic Logging Query

**Files:**

- Create: `/root/huhu/agent/combine-aiops-mcp/mcpstander/tests/test_aiops_observability_query_logs.py`
- Create: `/root/huhu/agent/combine-aiops-mcp/mcpstander/servers/aiops_observability/query/logs.py`
- Modify: `/root/huhu/agent/combine-aiops-mcp/mcpstander/servers/holmes_tools/aiops_observability_query.py`

- [ ] **Step 1: Write the failing Logging test group**

Cover UID-first DSL, name fallback metadata, container filter, any/all/phrase keywords, levels,
trace ID, max 50 records, deterministic duplicate removal, full decisive message preservation,
empty results and invalid oversized inputs.

- [ ] **Step 2: Run Logging tests and verify RED**

```bash
pytest -q tests/test_aiops_observability_query_logs.py
```

- [ ] **Step 3: Implement safe ES DSL generation**

The model supplies values, never raw DSL. Build:

- `@timestamp` range。
- exact namespace。
- UID `should` terms as the first query。
- exact Pod name and optional container。
- `match_phrase` clauses for keywords。
- exact level and trace ID field variants。
- `_source` allowlist。

If UID query returns zero and `allow_name_fallback=true`, run a second query and record:

```json
{"identity_basis": "name_time_fallback", "uid_query_hits": 0}
```

- [ ] **Step 4: Implement bounded real samples**

Deduplicate by timestamp + container + message hash. Return at most eight Agent-facing samples;
each decisive message may keep up to 1200 characters.

- [ ] **Step 5: Run Logging and contract tests**

```bash
pytest -q \
  tests/test_aiops_observability_query_contract.py \
  tests/test_aiops_observability_query_logs.py
```

## Task 4: Generic Tracing Query

**Files:**

- Create: `/root/huhu/agent/combine-aiops-mcp/mcpstander/tests/test_aiops_observability_query_tracing.py`
- Create: `/root/huhu/agent/combine-aiops-mcp/mcpstander/servers/aiops_observability/query/tracing.py`
- Modify: `/root/huhu/agent/combine-aiops-mcp/mcpstander/servers/holmes_tools/aiops_observability_query.py`

- [ ] **Step 1: Write the failing Tracing test group**

Cover Pod IP requirement, inbound/outbound SQL, protocol/status/code/duration/peer/resource/trace
filters, SQL escaping, LIMIT, DeepFlow flow samples, Tempo span samples, exact trace correlation,
and `empty` when the Pod never got an IP.

- [ ] **Step 2: Run Tracing tests and verify RED**

```bash
pytest -q tests/test_aiops_observability_query_tracing.py
```

- [ ] **Step 3: Implement safe ClickHouse SQL**

Only interpolate validated/escaped scalar values. Always include:

```sql
time >= toDateTime(..., 'UTC')
AND time <= toDateTime(..., 'UTC')
AND (ip4_0 = '<pod_ip>' OR ip4_1 = '<pod_ip>')
LIMIT <max_records>
FORMAT JSON
```

Direction and model-selected conditions add `AND` clauses; they never remove the Pod IP clause.

- [ ] **Step 4: Implement Tempo correlation**

Query Tempo only for explicit trace ID or complete IDs discovered from selected flows. Keep
`flows` and `spans` separate. Add `correlations` only when IDs match exactly.

- [ ] **Step 5: Run the complete MCP query module group**

```bash
pytest -q \
  tests/test_aiops_observability_query_contract.py \
  tests/test_aiops_observability_query_metrics.py \
  tests/test_aiops_observability_query_logs.py \
  tests/test_aiops_observability_query_tracing.py
```

## Task 5: MCP Server And Deployment

**Files:**

- Create: `/root/huhu/agent/combine-aiops-mcp/mcpstander/servers/aiops_observability_query_server.py`
- Modify: `/root/huhu/agent/combine-aiops-mcp/mcpstander/deploy/configmap.yaml`
- Modify: `/root/huhu/agent/combine-aiops-mcp/mcpstander/deploy/service.yaml`
- Modify: `/root/huhu/agent/combine-aiops-mcp/mcpstander/deploy/deployment.yaml`
- Modify: `/root/huhu/agent/combine-aiops-mcp/mcpstander/config/mcp_config.yaml`
- Modify: `/root/huhu/agent/combine-aiops-mcp/mcpstander/Dockerfile`
- Modify: `/root/huhu/agent/combine-aiops-mcp/mcpstander/tests/test_aiops_case_deploy.py`

- [ ] **Step 1: Add failing deploy assertions**

Assert port 8100 appears in ConfigMap, Service and Deployment, the server path exists, and the
container exposes the required port range.

- [ ] **Step 2: Run deploy tests and verify RED**

```bash
pytest -q tests/test_aiops_case_deploy.py
```

- [ ] **Step 3: Implement server entry and manifests**

Follow `aiops_observability_fine_server.py` logging and sanitization pattern. Add:

```yaml
- name: aiops-observability-query
  path: "servers/aiops_observability_query_server.py"
  port: 8100
  enabled: true
```

- [ ] **Step 4: Run the complete MCP grouped suite**

```bash
pytest -q \
  tests/test_aiops_observability_query_contract.py \
  tests/test_aiops_observability_query_metrics.py \
  tests/test_aiops_observability_query_logs.py \
  tests/test_aiops_observability_query_tracing.py \
  tests/test_aiops_case_deploy.py
```

## Task 6: Robusta Observation Contract

**Files:**

- Modify: `/root/huhu/agent/combine-aiops-mcp/robusta/tests/unit/aicall/test_observation_processing.py`
- Modify: `/root/huhu/agent/combine-aiops-mcp/robusta/app/core/context/observation.py`

- [ ] **Step 1: Write failing observation tests**

For each generic tool, assert:

- raw result is archived。
- structured result keeps `query`、`purpose`、`coverage`、`facts`、`samples` and refs。
- summary includes decisive values or exact log/trace sample。
- `empty`、`absent`、`weak`、`error` remain distinct。
- no extra LLM summary is used for deterministic query results。

- [ ] **Step 2: Run observation tests and verify RED**

```bash
pytest -q tests/unit/aicall/test_observation_processing.py
```

- [ ] **Step 3: Implement `_extract_observability_query`**

Add the three names to a dedicated tool set, not `AIOPS_CASE_TOOLS`. Validate the common
contract and produce a concise summary from facts/samples without inventing text.

- [ ] **Step 4: Run observation tests and verify GREEN**

```bash
pytest -q tests/unit/aicall/test_observation_processing.py
```

## Task 7: Evidence Autonomous Query Loop

**Files:**

- Modify: `/root/huhu/agent/combine-aiops-mcp/robusta/tests/unit/workflow/test_evidence_dynamic_stop.py`
- Modify: `/root/huhu/agent/combine-aiops-mcp/robusta/app/core/prompts.py`
- Modify: `/root/huhu/agent/combine-aiops-mcp/robusta/app/core/workflow/nodes/evidence_collector.py`

- [ ] **Step 1: Write failing Evidence behavior tests**

Assert:

- no autonomous config path injects `collect_aiops_case`。
- guidance names the three generic tools and Kubernetes tools。
- every query needs a diagnostic `purpose`。
- model may issue a second query after an ambiguous first result。
- ImagePull-like no-IP state may stop without forcing logs/tracing。
- context >=80% prevents more queries and lists unresolved targets。

- [ ] **Step 2: Run Evidence tests and verify RED**

```bash
pytest -q tests/unit/workflow/test_evidence_dynamic_stop.py
```

- [ ] **Step 3: Replace mandatory coarse prompt rules**

The prompt must say:

```text
先用 Kubernetes 强证据确认生命周期和异常实体。
对每个异常 Pod，至少选择一个能够改变根因判断的可观测性查询。
Metrics/Logging/Tracing 是否查询由生命周期和待验证问题决定，不要求凑齐三维。
第一轮结果仍有关键歧义时，可用新 purpose 和新条件继续补证。
```

Do not add scenario-specific Python routing.

- [ ] **Step 4: Adapt Evidence tool accounting**

Treat successful generic results with `coverage=present` as environment evidence. Treat empty,
absent, weak and error as explicit limitations. Preserve existing 80% context stop.

- [ ] **Step 5: Run Evidence and observation tests**

```bash
pytest -q \
  tests/unit/aicall/test_observation_processing.py \
  tests/unit/workflow/test_evidence_dynamic_stop.py
```

## Task 8: Runbooks And Runtime Switches

**Files:**

- Modify: `/root/huhu/agent/combine-aiops-mcp/robusta/deploy/configmap/runbooks.yaml`
- Modify: `/root/huhu/agent/combine-aiops-mcp/robusta/deploy/configmap/config.yaml`
- Modify: `/root/huhu/agent/combine-aiops-mcp/robusta/tests/unit/workflow/test_reporter_runbooks.py`

- [ ] **Step 1: Add failing Runbook/config assertions**

Assert the three Runbooks include:

```text
场景识别
诊断问题
可选观测维度
查询构造建议
证据边界
停止条件
```

Assert autonomous server is enabled and coarse/fine/broad Prometheus are disabled.

- [ ] **Step 2: Run Runbook tests and verify RED**

```bash
pytest -q tests/unit/workflow/test_reporter_runbooks.py
```

- [ ] **Step 3: Rewrite three Runbooks**

Use the recommendations in
`/root/huhu/agent/combine-aiops-mcp/data/specs/003-autonomous-observability-query/research.md`.
Do not include fixed full queries or tool order.

- [ ] **Step 4: Configure MCP switches**

Add:

```yaml
aiops-observability-query:
  description: "Pod 级自主可观测性查询：Qwen 选择 PromQL、日志和链路条件"
  config:
    url: "http://mcp-server-manager.mcp.svc.cluster.local:8100/sse"
    mode: "sse"
  enabled: true
```

- [ ] **Step 5: Run the complete Robusta module group**

```bash
pytest -q \
  tests/unit/aicall/test_observation_processing.py \
  tests/unit/workflow/test_evidence_dynamic_stop.py \
  tests/unit/workflow/test_reporter_runbooks.py
```

## Task 9: Deployment And Real Validation

**Files:**

- Create: `/root/huhu/agent/combine-aiops-mcp/robusta/testreports/autonomous-observability-query-20260721.md`

- [ ] **Step 1: Build and deploy mcpstander**

Use the repository's documented image build/import path, apply manifests, and verify:

```bash
kubectl rollout status deployment/mcp-server-manager -n mcp --timeout=180s
kubectl logs -n mcp deployment/mcp-server-manager --tail=300
```

The log must show the 8100 server and no startup exception.

- [ ] **Step 2: Smoke each tool against a real Pod**

Record actual parameters, query, output bytes, coverage, facts and samples.

- [ ] **Step 3: Build and deploy Robusta**

Use the existing deployment document and verify config includes only the intended autonomous
AIOps query server plus Kubernetes MCP for this mode.

- [ ] **Step 4: Run real Qwen diagnostics**

Run “我的集群现在有什么问题？” three times each for OOMKilled、ConfigError and
ImagePullBackOff. Record run IDs and Langfuse/session evidence.

- [ ] **Step 5: Audit outcomes**

Measure:

- executable query success >=90%。
- at least one autonomous follow-up query。
- no generic MCP fault-type branches。
- each tool result <=6KB。
- final numeric/log/trace facts trace to current tool output。
- context <80%。

## Task 10: Independent Review And Commits

**Files:**

- Update: `/root/huhu/agent/combine-aiops-mcp/data/agent-loop/autonomous-observability-query/`

- [ ] **Step 1: Run regression and source audit**

```bash
cd /root/huhu/agent/combine-aiops-mcp/mcpstander
rg -n 'OOMKilled|ImagePullBackOff|ConfigError|CrashLoopBackOff|Terminating' \
  servers/aiops_observability/query \
  servers/holmes_tools/aiops_observability_query.py

cd /root/huhu/agent/combine-aiops-mcp/robusta
git diff --check

cd /root/huhu/agent/combine-aiops-mcp
rg -n 'combine-aiops-mcp/data|AIOPS_DATASET_ROOT|AIOPS_COLLECT_SCRIPT|data/scripts' \
  mcpstander/servers/aiops_observability/query \
  mcpstander/servers/holmes_tools/aiops_observability_query.py \
  robusta/app/core robusta/deploy/configmap
```

- [ ] **Step 2: Request independent review**

Reviewer checks every acceptance criterion and returns ACCEPT/REWORK with evidence.

- [ ] **Step 3: Commit only relevant paths**

Do not add `.venv`, cache files, secrets, testreports history unrelated to this feature, or user
changes. Commit each repository separately and do not push without explicit instruction.
