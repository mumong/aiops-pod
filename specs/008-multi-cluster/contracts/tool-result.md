# Contract: MCP 工具的集群参数与结果字段

## 参数

所有可观测工具（`execute_pod_promql`、`query_pod_logs`、`query_pod_tracing`、`query_pod_topology`）、`prometheus_tool` 的 6 个工具、k8s-core 全部工具、`run_bash_command`、`kubectl_run_image` 增加可选参数：

```json
"cluster": {"type": "string", "description": "目标集群的规范名称或别名；单集群部署可省略"}
```

省略时：单集群部署为 `local`；多集群部署由 AIOps 注入（spec FR-007）。MCP 端收到未知集群 → `cluster_unknown` 错误，并附可用集群列表。

## 结果新增字段（顶层，其余字段不变）

| 字段 | 含义 |
|---|---|
| `cluster` | 实际查询的集群规范名称 |
| `backend` | `prometheus` / `elasticsearch` / `deepflow+tempo` / `victoriametrics` / `victorialogs_events` / `kubernetes` |

## 新增错误码

| code | 含义 |
|---|---|
| `cluster_unknown` | 注册表中没有这个集群 |
| `cluster_unreachable` | 集群离线，或隧道、runner 不可用 |
| `capability_missing` | 这个集群的后端没有该类数据 |
| `tunnel_auth_failed` | xnet 证书失效或被拒 |
| `runner_auth_failed` | runner 签名校验失败 |
| `policy_denied` | 被 runner 的命令规则拒绝 |

## victoria 后端下 query_pod_logs 的结果

- `log_source`: `k8s_events`
- `coverage`: `partial`
- 每条记录：`time`、`type`（Normal/Warning）、`reason`、`message`、`count`、`involved_kind`、`involved_name`
- 附说明："该集群未采集容器日志；需要容器日志请使用 kubectl_logs"

## 新增工具 list_clusters

无参数。返回 `[{name, aliases, access, observability, online, capabilities}]`。
