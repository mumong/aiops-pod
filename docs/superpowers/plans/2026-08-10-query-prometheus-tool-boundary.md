# Query Prometheus Tool Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `/query` 使用通用 Prometheus MCP 查询 node/cluster 指标，同时让 `/ask` Pod 异常诊断继续只使用 Pod-scoped `execute_pod_promql`。

**Architecture:** Backend 启用现有 8095 Prometheus MCP，由 Query direct layer 使用 instant/range 工具；Evidence 节点在工具暴露边界硬性排除该 MCP 的八个通用工具。Runbook、Query prompt、Backend MCP 描述和 MCP Tool description 同时声明用途边界。

**Tech Stack:** Python 3.12、LangGraph/LangChain MCP adapter、MCP Python SDK、Pytest/Unittest、Kubernetes ConfigMap。

---

### Task 1: Backend 配置和 Query 指引

**Files:**
- Modify: `tests/unit/workflow/test_fast_paths.py`
- Modify: `deploy/configmap/config.yaml`
- Modify: `deploy/configmap/runbooks.yaml`
- Modify: `app/core/prompts.py`

- [ ] **Step 1: 写配置、Prompt 和 Runbook 失败测试**

在 `test_deployed_config_enables_autonomous_observability_and_disables_compatibility_servers` 中增加：

```python
prometheus = app_config["mcp_servers"]["prometheus_tool"]
assert prometheus["enabled"] is True
assert prometheus["config"]["url"] == "http://mcp-server-manager.mcp.svc.cluster.local:8095/sse"
assert "/query" in prometheus["description"]
assert "execute_pod_promql" in prometheus["description"]
```

在 Query prompt 契约测试中要求以下文字存在，并解析 `runbooks.yaml` 检查同样边界：

```python
assert "execute_prometheus_instant_query" in direct_prompt
assert "execute_prometheus_range_query" in direct_prompt
assert "execute_pod_promql" in direct_prompt

runbook_configmap = yaml.safe_load(Path("deploy/configmap/runbooks.yaml").read_text())
query_runbook = runbook_configmap["data"]["private-k8s-query-promql-reference.md"]
assert "execute_prometheus_instant_query" in query_runbook
assert "execute_prometheus_range_query" in query_runbook
assert "execute_pod_promql" in query_runbook
```

- [ ] **Step 2: 运行测试确认 RED**

Run:

```bash
pytest -q tests/unit/workflow/test_fast_paths.py -k 'query_direct_prompt_boundaries or deployed_config_enables_autonomous'
```

Expected: FAIL，因为 `prometheus_tool.enabled` 仍为 false，且 Prompt/Runbook 未声明工具分工。

- [ ] **Step 3: 最小实现配置和文字边界**

将 `prometheus_tool.enabled` 改为 true，并把 description 改为：

```yaml
description: "Query-only Prometheus MCP - 仅供 /query 的 node/cluster 通用 PromQL；/ask Pod 异常诊断必须使用 execute_pod_promql"
```

Query prompt 和 Runbook 增加：

```text
- node/cluster 通用指标只使用 execute_prometheus_instant_query 或 execute_prometheus_range_query。
- execute_pod_promql 要求精确 namespace/pod scope，供 /ask Pod 异常诊断使用，不得用于 node/cluster Query。
```

- [ ] **Step 4: 运行测试确认 GREEN**

Run:

```bash
pytest -q tests/unit/workflow/test_fast_paths.py -k 'query_direct_prompt_boundaries or deployed_config_enables_autonomous'
```

Expected: PASS。

### Task 2: `/ask` Evidence 硬隔离通用 Prometheus 工具

**Files:**
- Modify: `tests/unit/workflow/test_evidence_dynamic_stop.py`
- Modify: `app/core/workflow/nodes/evidence_collector.py`

- [ ] **Step 1: 写失败测试**

构造含通用工具和 Pod 工具的节点，即使 evidence plan 明确写入通用工具，也必须屏蔽通用工具：

```python
node.tools = [
    SimpleNamespace(name="execute_prometheus_instant_query"),
    SimpleNamespace(name="execute_prometheus_range_query"),
    SimpleNamespace(name="get_metric_names"),
    SimpleNamespace(name="execute_pod_promql"),
]
blocked = node._blocked_tools_for_preplanned_execution([
    {"tool": "execute_prometheus_instant_query", "acceptable_tools": ["execute_prometheus_range_query"]},
    {"tool": "execute_pod_promql", "acceptable_tools": ["execute_pod_promql"]},
])
assert "execute_prometheus_instant_query" in blocked
assert "execute_prometheus_range_query" in blocked
assert "get_metric_names" in blocked
assert "execute_pod_promql" not in blocked
```

- [ ] **Step 2: 运行测试确认 RED**

Run:

```bash
pytest -q tests/unit/workflow/test_evidence_dynamic_stop.py -k query_only_prometheus
```

Expected: FAIL，因为计划当前可以把通用 Prometheus 工具加入 allowed_tools。

- [ ] **Step 3: 最小实现硬隔离**

在 `EvidenceCollectorNode` 中定义：

```python
_QUERY_ONLY_PROMETHEUS_TOOLS = {
    "list_prometheus_rules", "get_metric_names", "get_label_values",
    "get_all_labels", "get_series", "get_metric_metadata",
    "execute_prometheus_instant_query", "execute_prometheus_range_query",
}
```

在 `_blocked_tools_for_preplanned_execution` 汇总计划允许项后执行：

```python
allowed_tools.difference_update(self._QUERY_ONLY_PROMETHEUS_TOOLS)
```

- [ ] **Step 4: 运行测试确认 GREEN**

Run:

```bash
pytest -q tests/unit/workflow/test_evidence_dynamic_stop.py -k query_only_prometheus
```

Expected: PASS。

### Task 3: MCP Tool description 契约

**Files:**
- Modify: `../mcpstander/tests/test_prometheus_error.py`
- Modify: `../mcpstander/servers/holmes_tools/prometheus.py`
- Modify: `../mcpstander/README.md`

- [ ] **Step 1: 写失败测试**

```python
def test_all_prometheus_tools_are_marked_query_only(self):
    for tool in prometheus.TOOLS:
        description = tool.description.lower()
        self.assertIn("/query", description)
        self.assertIn("/ask", description)
        self.assertIn("execute_pod_promql", description)
```

- [ ] **Step 2: 运行测试确认 RED**

Run:

```bash
python -m unittest tests.test_prometheus_error.PrometheusErrorTests.test_all_prometheus_tools_are_marked_query_only
```

Expected: FAIL，当前 description 仅描述 API 功能。

- [ ] **Step 3: 最小实现 MCP 描述**

定义共享后缀并追加到八个 Tool description：

```python
QUERY_ONLY_BOUNDARY = (
    " AIOps boundary: use only in /query for general node/cluster Prometheus queries; "
    "do not use in /ask Pod diagnosis, where execute_pod_promql is required."
)
```

README 的 8095 行同步标记 Query-only；8100 行标记 `/ask` Pod-scoped。

- [ ] **Step 4: 运行测试确认 GREEN**

Run:

```bash
python -m unittest tests.test_prometheus_error
```

Expected: PASS。

### Task 4: 回归、部署和真实验收

**Files:**
- Modify: `VERSION`
- Modify: `deploy/k8s-simple.yaml`
- Modify: `../mcpstander/VERSION`
- Modify: `../mcpstander/deploy/deployment.yaml`

- [ ] **Step 1: 运行 Backend 和 MCP 定向测试**

```bash
pytest -q tests/unit/workflow/test_fast_paths.py tests/unit/workflow/test_evidence_dynamic_stop.py
python -m unittest tests.test_prometheus_error
```

Expected: 全部 PASS。

- [ ] **Step 2: 运行两个仓库全量测试**

```bash
pytest -q
cd ../mcpstander && python -m unittest discover -s tests
```

Expected: 0 failed / 0 errors。

- [ ] **Step 3: 递增 Backend/MCP 版本并部署**

同步更新 VERSION 与各自 Deployment 镜像标签，然后分别运行：

```bash
make build push deploy
cd ../mcpstander && make build push deploy
```

Expected: 两个 rollout 成功，Pod imageID 与新 Harbor digest 一致。

- [ ] **Step 4: 真实 Query 验收**

提交“查询集群每个节点 CPU 和内存使用率”，检查新 run archive：

```text
execute_prometheus_instant_query -> semantic_success=true
query_result.rows -> master/node1/node2 独立行
```

Expected: 不再出现 `execute_pod_promql missing_pod_scope`。

- [ ] **Step 5: 真实 `/ask` Pod 诊断边界验收**

对一个明确 Pod 发起只读诊断，检查 evidence 工具事件：

```text
execute_pod_promql -> tool_result
execute_prometheus_instant_query/range_query -> 0 次
```

Expected: Pod 专属指标路径保持不变。
