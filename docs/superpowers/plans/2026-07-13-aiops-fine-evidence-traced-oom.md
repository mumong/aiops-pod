# AIOps Fine-Grained Evidence and Traced OOM Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 Robusta Agent 自主调用 AIOps MCP 后直接获得真实、可读、受限大小的 Metrics、Logging、Tracing 和 Topology 细粒度证据，并在最终报告中基于这些原始数据构建因果链。

**Architecture:** mcpstander 在完整 case package 之外新增 `dimension_details` 首屏摘要，Prometheus 使用窗口查询生成趋势，ES/DeepFlow/Tempo/Topology 生成少量原始样本；Robusta ObservationProcessor 按维度保留这些安全字段，Prompt 引导但不强制 Qwen 调用工具。统一 OOM workload 通过真实请求、W3C traceparent、OTLP span 和缓慢内存增长产生可关联的四维证据。

**Tech Stack:** Python 3.10/3.12、MCP Python SDK、requests、Prometheus HTTP API、Elasticsearch/Filebeat、DeepFlow ClickHouse、Tempo/OTLP HTTP、Kubernetes YAML、pytest/unittest、Shell。

---

## File Map

### mcpstander

- `servers/aiops_observability/collectors/prometheus.py`
  - 增加 instant/range 查询、目标容器过滤、重复序列归并和趋势摘要。
- `servers/aiops_observability/collectors/elasticsearch.py`
  - 生成带时间戳的有限日志样本。
- `servers/aiops_observability/collectors/deepflow.py`
  - 生成有限 L7 flow 和 eBPF call-chain 样本。
- `servers/aiops_observability/collectors/tempo.py`
  - 生成有限 span 样本。
- `servers/aiops_observability/case_builder.py`
  - 汇总 `dimension_details`。
- `servers/aiops_observability/topology.py`
  - 生成实体和边的人类可读摘要。
- `tests/test_aiops_observability_collectors.py`
  - collector 分组测试。
- `tests/test_aiops_case_tool.py`
  - coarse MCP 合同与反泄漏测试。

### robusta

- `app/core/context/observation.py`
  - 白名单保留 `dimension_details` 和 evidence payload 的诊断字段。
- `app/core/prompts.py`
  - 将强制调用改为 Qwen 自主选择；强制最终报告引用具体原始证据。
- `app/core/workflow/nodes/evidence_collector.py`
  - 移除确定性 `collect_aiops_case` 计划注入。
- `tests/unit/aicall/test_observation_processing.py`
  - 细粒度摘要裁剪和反泄漏测试。
- `tests/unit/workflow/test_fast_paths.py`
  - 工具自主选择行为测试。
- `deploy/testcases/aiops-traced-oom.yaml`
  - 唯一标准 OOM 测试场景。
- `scripts/aiops-traced-oom.sh`
  - apply/status/logs/verify/cleanup。
- `docs/aiops-traced-oom-test-environment.md`
  - 中文手工部署和验证文档。

## Task 1: Prometheus Range Evidence

**Files:**
- Modify: `/root/huhu/agent/combine-aiops-mcp/mcpstander/servers/aiops_observability/collectors/prometheus.py`
- Modify: `/root/huhu/agent/combine-aiops-mcp/mcpstander/tests/test_aiops_observability_collectors.py`

- [ ] **Step 1: 添加 range 和趋势单元测试**

测试必须覆盖：

```python
def test_range_summary_filters_pause_and_deduplicates_scrapers():
    # 三套 scraper 返回同一 business-api 序列，同时包含 POD/pause 序列。
    # 期望只生成一条 business-api highlight。
    assert highlights[0]["container"] == "business-api"
    assert highlights[0]["max"] == "63.0Mi"


def test_range_summary_includes_limit_and_ratio():
    assert highlight["limit"] == "64.0Mi"
    assert highlight["max_limit_ratio"] == 0.9844


def test_range_empty_does_not_claim_growth():
    assert result.coverage == "present"
    assert result.evidence[0].payload["highlights"] == []
```

- [ ] **Step 2: 运行 collector 测试确认失败**

```bash
cd /root/huhu/agent/combine-aiops-mcp/mcpstander
.venv/bin/python -m pytest tests/test_aiops_observability_collectors.py -q
```

预期：新增测试因 `_query_range`、趋势摘要或 `highlights` 不存在而失败。

- [ ] **Step 3: 实现 range 查询和摘要**

实现接口：

```python
def _query_range(url: str, query: str, start: str, end: str, step: int, timeout: int) -> dict[str, Any]:
    ...


def _memory_highlights(
    range_results: list[dict[str, Any]],
    limit_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    ...
```

规则：

- 目标容器标签必须非空且不等于 `POD`。
- 排除 pause image。
- 按 `namespace/pod/container` 归并重复 scraper。
- 输出 start/max/last/limit/max_limit_ratio 和最多 5 个采样点。
- `collect_prometheus` 新增 `start/end/step_seconds` 参数。

- [ ] **Step 4: 运行 collector 测试**

```bash
.venv/bin/python -m pytest tests/test_aiops_observability_collectors.py -q
```

预期：Prometheus 新旧测试全部通过。

## Task 2: Bounded Logs, Traces and Topology Details

**Files:**
- Modify: `/root/huhu/agent/combine-aiops-mcp/mcpstander/servers/aiops_observability/collectors/elasticsearch.py`
- Modify: `/root/huhu/agent/combine-aiops-mcp/mcpstander/servers/aiops_observability/collectors/deepflow.py`
- Modify: `/root/huhu/agent/combine-aiops-mcp/mcpstander/servers/aiops_observability/collectors/tempo.py`
- Modify: `/root/huhu/agent/combine-aiops-mcp/mcpstander/servers/aiops_observability/topology.py`
- Modify: `/root/huhu/agent/combine-aiops-mcp/mcpstander/tests/test_aiops_observability_collectors.py`

- [ ] **Step 1: 添加 bounded detail 测试**

断言：

```python
assert len(log_samples) <= 8
assert log_samples[0]["timestamp"]
assert log_samples[0]["message"]
assert len(flow_samples) <= 5
assert flow_samples[0]["request"] == "GET /allocate?mib=2"
assert flow_samples[0]["trace_id"]
assert len(span_samples) <= 3
assert topology_details["edges"][0]["relationship"] == "Service --selects--> Pod"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
.venv/bin/python -m pytest tests/test_aiops_observability_collectors.py -q
```

- [ ] **Step 3: 实现维度摘要函数**

每个 collector evidence payload 增加：

```python
payload={
    "records": records[:10],
    "samples": bounded_samples,
    "source": source_desc,
}
```

DeepFlow sample 保留：

```text
timestamp/src/dst/protocol/request/response_code/duration_us/trace_id/span_id
```

Tempo sample 保留：

```text
trace_id/service/name/start/end/attributes
```

Topology 新增：

```python
def topology_details(entities, edges, *, max_entities=10, max_edges=12) -> dict[str, Any]:
    ...
```

- [ ] **Step 4: 运行 collector 测试**

```bash
.venv/bin/python -m pytest tests/test_aiops_observability_collectors.py -q
```

预期：全部通过。

## Task 3: MCP `dimension_details` Contract

**Files:**
- Modify: `/root/huhu/agent/combine-aiops-mcp/mcpstander/servers/aiops_observability/case_builder.py`
- Modify: `/root/huhu/agent/combine-aiops-mcp/mcpstander/tests/test_aiops_case_tool.py`
- Modify: `/root/huhu/agent/combine-aiops-mcp/mcpstander/tests/test_aiops_observability_contract.py`

- [ ] **Step 1: 添加 case summary 合同测试**

```python
assert payload["dimension_details"]["metrics"]["highlights"]
assert payload["dimension_details"]["logs"]["samples"]
assert payload["dimension_details"]["tracing"]["flows"]
assert payload["dimension_details"]["topology"]["edges"]
assert len(json.dumps(payload["dimension_details"], ensure_ascii=False)) <= 6000
```

同时断言不包含：

```text
root_cause_label
expected_remediation
labels
```

- [ ] **Step 2: 运行 MCP 分组测试确认失败**

```bash
.venv/bin/python -m pytest \
  tests/test_aiops_case_tool.py \
  tests/test_aiops_observability_contract.py -q
```

- [ ] **Step 3: 实现 `dimension_details`**

在 `case_summary` 中读取 case evidence 和 topology，返回：

```python
"dimension_details": {
    "metrics": _metric_details(...),
    "logs": _log_details(...),
    "tracing": _tracing_details(...),
    "topology": topology_details(...),
}
```

要求 coverage 与 `case.yaml` 一致，所有样本带 evidence ref，并进行总字符裁剪。

- [ ] **Step 4: 运行 mcpstander AIOps 测试组**

```bash
.venv/bin/python -m pytest \
  tests/test_aiops_observability_collectors.py \
  tests/test_aiops_case_tool.py \
  tests/test_aiops_observability_contract.py \
  tests/test_aiops_observability_fine.py -q
```

预期：全部通过。

## Task 4: Robusta Fine Evidence Consumption

**Files:**
- Modify: `/root/huhu/agent/combine-aiops-mcp/robusta/app/core/context/observation.py`
- Modify: `/root/huhu/agent/combine-aiops-mcp/robusta/tests/unit/aicall/test_observation_processing.py`

- [ ] **Step 1: 添加 ObservationProcessor 测试**

构造包含 `dimension_details` 的 `collect_aiops_case` 返回，断言：

```python
assert structured["dimension_details"]["metrics"]["highlights"][0]["max"] == "63.2Mi"
assert "allocated_mib=50" in summary
assert "GET /allocate" in summary
assert "Service --selects--> Pod" in summary
assert len(summary) <= processor.max_observation_chars
```

构造 `get_aiops_case_evidence` payload，断言仅保留允许的 sample/flow/span 字段，不保留
任意大 payload 或 evaluator 字段。

- [ ] **Step 2: 运行 ObservationProcessor 测试确认失败**

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
pytest tests/unit/aicall/test_observation_processing.py -q
```

- [ ] **Step 3: 实现白名单裁剪**

增加私有函数：

```python
def _sanitize_aiops_dimension_details(self, payload: dict[str, Any]) -> dict[str, Any]:
    ...


def _sanitize_aiops_evidence_payload(self, dimension: str, payload: dict[str, Any]) -> dict[str, Any]:
    ...
```

按维度保留：

- metrics: metric/container/start/max/last/limit/max_limit_ratio/samples/evidence_ref
- logs: timestamp/message/container/evidence_ref
- tracing: timestamp/src/dst/protocol/request/code/duration/trace_id/span_id
- spans: trace_id/service/name/attributes/evidence_ref
- topology: entities/relationship/directness/confidence/evidence_refs

- [ ] **Step 4: 运行 ObservationProcessor 测试**

```bash
pytest tests/unit/aicall/test_observation_processing.py -q
```

预期：全部通过。

## Task 5: Qwen Autonomous Tool Selection and Report Grounding

**Files:**
- Modify: `/root/huhu/agent/combine-aiops-mcp/robusta/app/core/prompts.py`
- Modify: `/root/huhu/agent/combine-aiops-mcp/robusta/app/core/workflow/nodes/evidence_collector.py`
- Modify: `/root/huhu/agent/combine-aiops-mcp/robusta/tests/unit/workflow/test_fast_paths.py`

- [ ] **Step 1: 替换强制注入测试**

删除 `test_inject_aiops_case_plan_item_deterministic_routing`，增加：

```python
def test_evidence_plan_is_not_modified_to_force_aiops_case():
    assert node._normalize_evidence_plan(base_plan, handoff) == base_plan
```

并断言 Prompt 包含：

```text
由模型根据诊断需要决定是否调用 collect_aiops_case
需要资源趋势、集中日志、调用链或拓扑时优先调用
```

- [ ] **Step 2: 运行 workflow 测试确认失败**

```bash
pytest \
  tests/unit/workflow/test_fast_paths.py \
  tests/unit/workflow/test_structured_schemas.py -q
```

- [ ] **Step 3: 移除强制注入并更新 Prompt**

- 删除两处 `_inject_aiops_case_plan_item(...)` 调用和对应方法。
- Prompt 从“第一条必须”改为模型自主选择。
- 最终报告规则要求 present 维度至少引用一条具体样本和 evidence ref。
- 禁止从 `series/records/entities` 计数推导趋势或健康结论。

- [ ] **Step 4: 运行 Robusta 分组测试**

```bash
pytest \
  tests/unit/aicall/test_observation_processing.py \
  tests/unit/workflow/test_fast_paths.py \
  tests/unit/workflow/test_structured_schemas.py \
  tests/unit/workflow/test_evidence_dynamic_stop.py -q
```

预期：全部通过。

## Task 6: Deployable Traced OOM Environment

**Files:**
- Create: `/root/huhu/agent/combine-aiops-mcp/robusta/deploy/testcases/aiops-traced-oom.yaml`
- Create: `/root/huhu/agent/combine-aiops-mcp/robusta/scripts/aiops-traced-oom.sh`
- Create: `/root/huhu/agent/combine-aiops-mcp/robusta/docs/aiops-traced-oom-test-environment.md`
- Delete after migration: `/root/huhu/agent/combine-aiops-mcp/robusta/tmp-oomkilled-business-pod.yaml`

- [ ] **Step 1: 创建 manifest 静态验证测试或命令**

验证目标：

```bash
kubectl apply --dry-run=client -f deploy/testcases/aiops-traced-oom.yaml
bash -n scripts/aiops-traced-oom.sh
```

- [ ] **Step 2: 创建统一 workload**

Manifest 包含：

```text
Namespace/aiops-temp
Service/aiops-oom-business
Deployment/aiops-oom-business
Deployment/aiops-oom-driver
```

业务 Pod：

- 80Mi memory limit。
- `/allocate?mib=2` 每次分配 2MiB。
- 解析 `traceparent`。
- 输出 JSON 日志。
- 向 `http://lgtm.xnet.svc:4318/v1/traces` 发送 OTLP JSON span。

Driver：

- 每 5 秒发送一次请求。
- 生成合法 W3C trace ID/span ID。
- 打印请求结果。
- 业务 Pod不可用时继续重试。

- [ ] **Step 3: 创建管理脚本**

```bash
scripts/aiops-traced-oom.sh apply
scripts/aiops-traced-oom.sh status
scripts/aiops-traced-oom.sh logs
scripts/aiops-traced-oom.sh verify
scripts/aiops-traced-oom.sh cleanup
```

`apply` 删除：

```text
Pod/aiops-temp/aiops-oom-business
Namespace/aiops-dfotel-test
```

再部署统一 manifest。

- [ ] **Step 4: 编写中文文档**

文档说明：

- 一键部署、状态查看、日志查看、采集和清理命令。
- DeepFlow flow 与 Tempo span 的区别。
- 无埋点、traceparent、完整 OTel span 三种能力边界。

- [ ] **Step 5: 静态验证**

```bash
kubectl apply --dry-run=client -f deploy/testcases/aiops-traced-oom.yaml
bash -n scripts/aiops-traced-oom.sh
```

## Task 7: Module Verification and Deployment

**Files:**
- Use without modification: `/root/huhu/agent/combine-aiops-mcp/mcpstander/Makefile`
- Use without modification: `/root/huhu/agent/combine-aiops-mcp/robusta/Makefile`

- [ ] **Step 1: 运行 mcpstander 模块测试**

```bash
cd /root/huhu/agent/combine-aiops-mcp/mcpstander
.venv/bin/python -m pytest \
  tests/test_aiops_observability_collectors.py \
  tests/test_aiops_case_tool.py \
  tests/test_aiops_observability_contract.py \
  tests/test_aiops_observability_fine.py -q
```

- [ ] **Step 2: 运行 Robusta 模块测试**

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
pytest \
  tests/unit/aicall/test_observation_processing.py \
  tests/unit/workflow/test_fast_paths.py \
  tests/unit/workflow/test_structured_schemas.py \
  tests/unit/workflow/test_evidence_dynamic_stop.py -q
```

- [ ] **Step 3: 部署 mcpstander**

```bash
cd /root/huhu/agent/combine-aiops-mcp/mcpstander
make build-push
make deploy
kubectl rollout status deployment/mcp-server-manager -n mcp --timeout=120s
kubectl logs -n mcp deployment/mcp-server-manager --tail=120
```

确认日志中 coarse AIOps MCP server 启动在 8089，随后通过 Robusta 的 MCP client
实际调用验证工具列表和 `collect_aiops_case` 返回。

- [ ] **Step 4: 部署 Robusta**

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
make build
make push
make deploy
kubectl rollout status deployment/aiops-copilot -n aiops --timeout=300s
kubectl get configmap -n aiops aiops-copilot-config -o yaml | \
  rg -n 'aiops-case-coarse|8089|enabled'
```

确认 `aiops-case-coarse` 仍为 enabled，且没有启用 fine server。

- [ ] **Step 5: 部署统一测试环境**

```bash
cd /root/huhu/agent/combine-aiops-mcp/robusta
scripts/aiops-traced-oom.sh apply
scripts/aiops-traced-oom.sh verify
```

预期：

- 业务 Pod 反复 OOMKilled。
- Driver Pod Running。
- 日志出现非空 trace_id/span_id。

## Task 8: Live End-to-End Acceptance

- [ ] **Step 1: 真实调用 MCP**

对新异常 Pod 调用 `collect_aiops_case`，验证：

```text
metrics.highlights 包含 range max 和 limit
logs.samples 包含 timestamp/trace_id/allocated_mib
tracing.flows 包含 GET /allocate 和 trace_id
tracing.spans 包含 Tempo span
topology.edges 包含 Service selects Pod、owner chain 和 caller relation
```

- [ ] **Step 2: 运行 Robusta 诊断**

```bash
curl --no-buffer -G "http://10.2.0.48:30800/ask" \
  --data-urlencode "q=我的集群现在有什么问题？"
```

- [ ] **Step 3: 审计运行归档**

检查 run archive：

- Qwen 是否自主选择 `collect_aiops_case`。
- Observation summary 是否包含具体指标值、日志、flow/span 和拓扑边。
- RCA 是否把 trace request、日志内存增长、Prometheus 趋势、OOMKilled 连成因果链。
- 最终报告是否引用 evidence ref。
- empty/weak 数据是否被诚实表达。

- [ ] **Step 4: 最终回归**

确认：

- 运行时不依赖 `data`。
- 只有一种异常测试场景。
- 用户现有无关修改未被覆盖。
- 两仓库 Git diff 只包含本功能文件。
