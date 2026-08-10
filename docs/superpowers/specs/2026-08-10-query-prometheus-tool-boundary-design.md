# Query Prometheus 工具边界设计

## 背景与根因

真实运行 `413b491b3bf84d17` 的问题是“查询集群各节点 CPU 和内存使用率”。
Query Agent 正确取得节点级标准 PromQL，但 Backend 部署配置关闭了 `prometheus_tool`
（MCP `8095`），因此只能误用要求精确 namespace/pod scope 的
`execute_pod_promql`。MCP 随后以 `missing_pod_scope` 正确拒绝 node 级 PromQL，
最终没有可渲染的 `query_result`。

## 目标

1. `/query` 可以使用通用 Prometheus MCP 执行 node/cluster 级 instant/range PromQL。
2. `/ask` Pod 异常诊断继续使用 `execute_pod_promql`，不回退到无 Pod scope 的通用查询。
3. Query Runbook、Backend MCP 配置描述和 MCP Tool description 都明确这条边界。
4. 保留现有 Pod 专属查询的 scope 校验、Fact Ledger 和三维可观测性门控。

## 方案

### Backend 工具注册

启用现有 `prometheus_tool`，继续连接
`http://mcp-server-manager.mcp.svc.cluster.local:8095/sse`。不新增 MCP 服务，
不修改 Prometheus 地址，也不放宽 `execute_pod_promql` 的 scope 校验。

### 工作流隔离

- Query direct 的 layer 节点保留通用 Prometheus instant/range 查询能力。
- 非 Query 的 layer 节点沿用现有工具白名单，本来就不会获得通用 Prometheus 工具。
- Evidence 节点把通用 Prometheus MCP 的 discovery/instant/range 工具设为 Query-only，
  即使模型把它们写入诊断计划也不会暴露给 `/ask`；Pod Metrics 仍由
  `execute_pod_promql` 完成。

### 提示与说明

- Query prompt 明确 node/cluster 指标使用
  `execute_prometheus_instant_query` / `execute_prometheus_range_query`。
- `private-k8s-query-promql-reference.md` 增加“工具选择”章节：只用于 `/query`；
  Pod 异常诊断必须使用 `execute_pod_promql`。
- Prometheus MCP 的八个 Tool description 均标记为 `/query` 通用 Prometheus 能力，
  并明确禁止用于 `/ask` Pod 异常诊断。
- Backend `mcp_servers.prometheus_tool.description` 使用同样措辞，避免运维配置误解。

## 测试与验收

1. 配置测试：`prometheus_tool.enabled=true`，URL/模式不变，description 含 Query-only 边界。
2. 工作流测试：Query prompt/runbook 点名通用工具；Evidence 工具集合排除通用 Prometheus、保留 `execute_pod_promql`。
3. MCP 契约测试：八个 Prometheus Tool description 均包含 `/query` 和 Pod 诊断替代工具说明。
4. 回归测试：Backend 和 MCPStander 定向测试、各自全量测试通过。
5. 真实验证：部署新版本后再次询问节点 CPU/内存，归档中出现成功的
   `execute_prometheus_instant_query`，最终结果按节点呈现；再运行一个 Pod 异常诊断，
   Metrics 仍由 `execute_pod_promql` 采集。
