# Pod 生命周期事实契约

## 目的与边界

`query_pod_lifecycle` 是 Kubernetes MCP 的可选只读工具，供快速查询和自主深度诊断使用。
Agent 自主选择查询范围、是否调用、后续取证及何时结束；不新增固定检测流程、异常筛选器或修复脚本。
旧 kubectl 工具不变。当前版本只定义 Pod 的生命周期事实，未给其他资源虚构统一状态字段。

## 输入与输出

输入支持 `namespace`、精确 `pod`、`label_selector`、`window_minutes`（默认 10 分钟，可显式覆盖）、
`page_size`（默认 50，最大 100）、`continue_token`。查询单 Pod 必须指定 namespace。

`pod-lifecycle.v1` 返回以下事实，不返回健康评分或根因：

| 层级 | 字段 |
| --- | --- |
| 采集 | source、observed_at、scope、window、resource_version |
| 覆盖 | coverage、returned_count、next_continue_token、remaining_item_count |
| Pod | namespace、name、uid、created_at、deletion_timestamp、node、phase、reason、conditions |
| 容器 | name、role（app/init/ephemeral）、status_observed、ready、resources |
| 生命周期 | state、last_state（原因、退出码、信号、起止时间）、restart_count_total |
| 时间解释 | latest_observed_termination_at、termination_within_window、restart_count_in_window |

`termination_within_window=true` 仅表示当前/上次终止的已知时间落入窗口，
不等于异常：Completed 的初始化容器也可能满足。由 Agent 结合退出原因和任务目标解释。
`restart_count_total` 是 Kubernetes 累计计数；`restart_count_in_window` 固定为 null，
因为 Pod 快照无法证明完整历史。缺失、非法、未来或无时区的终止时间不被当作“没有近期重启”。

例如当前 Running/Ready 的容器，仍会保留：

```json
{
  "ready": true,
  "restart_count_total": 2,
  "last_state": {"terminated": {"reason": "OOMKilled", "exitCode": 137,
    "finishedAt": "2026-10-09T02:48:17Z"}},
  "termination_within_window": true,
  "restart_count_in_window": null
}
```

## 分页、错误与上下文

- 不按 phase/ready 筛选 Pods，避免漏掉已经恢复的容器。
- `coverage=partial` 表示还有分页，Agent 使用相同范围和 continue token 继续查询。
  最后一页的 present 只描述该页，不代表 Agent 已读取所有前页。
- 成功无匹配项是 `coverage=empty`；权限、API、超时错误是 `status=error, coverage=unknown`。
- 每页有自己的 observed_at/window；跨页使用 API resourceVersion 保持列表快照一致。
- 后端归档并原样传递当前页，不再进行表格摘要或单工具 LLM 摘要。
  全局会话上下文压缩策略未改变；分页也不等于严格 token 上限。
- 只投影必要状态和资源配置，不包含环境变量、Secret、命令或完整 annotations。
- 使用 kubectl argv 和 API 分页，无 shell 插值，不改变 RBAC。raw API 请求在集群内
  使用临时 0600 kubeconfig 引用挂载的 ServiceAccount tokenFile 和 CA；不把 token 放进参数。
  显式 KUBECONFIG 或默认本地 kubeconfig 优先，保留原有集群上下文。

## 验证与回退

MCP 测试覆盖恢复后的 OOM、10 分钟边界、显式窗口覆盖、旧/未知时间、初始化/临时容器、正常完成、分页、
API 失败及原工具定义不变。后端测试覆盖大页原样传递、工具可用性和错误语义。
单元测试保证事实契约，不保证模型每次都会选对工具或正确诊断，必须配合真实对话验收。

当前部署 MCP `7.0.33-pod-lifecycle-10m-20261009` 和后端 `11.0.204-pod-lifecycle-20261009`。
默认窗口从 30 分钟调整为 10 分钟，累计重启次数仍为生命周期累计值；显式指定窗口仍有效。
发布基于当时线上不可变镜像，仅复制本轮相关模块，未打包 MCP 工作区其他未发布改动。
回退时将两个 Deployment 镜像分别恢复至之前实际在线的 MCP `7.0.31` 和后端
`11.0.203-query-goal-20261009`；不要删除 namespace、PVC 或 Secret。
