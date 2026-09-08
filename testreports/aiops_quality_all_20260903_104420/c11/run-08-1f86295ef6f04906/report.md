## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | {'container': 'app', 'reason': 'Error'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase: Running`, `container.ready: False`, `last_terminated_reason: Error` | 显示容器处于非终止状态但不可用，存在“假活”或僵死状态 |
| 2 | K8s State | Kubernetes | `container.exit_code: 137`, `restart_count: 0` | 容器曾异常退出（137 通常为 OOMKilled），但无重启历史，与当前 Running 状态矛盾 |
| 3 | K8s Config | Kubernetes | `resource_limit.cpu: 200m`, `resource_limit.memory: 96Mi` | 资源限制配置较低，具备引发 OOMKilled 的环境条件 |
| 4 | Metric | Prometheus | `kube_pod_status_phase: 1` (Running), `container_restarts: 0` | 确认最近（22:44:03）Pod 仍为 Running 且未重启，佐证当前无活跃终止过程 |
| 5 | Logging | Elasticsearch | `log.message: "request completed"` (HTTP 200, `/work`), trace_ids: `f97154...`, `75c402...` | 业务层面正常处理请求，无报错日志，排除应用层常规崩溃 |
| 6 | Tracing | Tempo/Deepflow | Flow: `GET /work` (200 OK, 172.16.104.25 → 23), 关联 trace_id: `75c4028b...` | 网络与链路正常，进一步证实非终止状态下仍有流量通过 |

**证据说明：**
1. **状态矛盾**：事实 #1 与 #2 显示 Pod 处于 Running 状态且无重启，但 exitCode 为 137 且 last_terminated_reason 为 Error，这通常发生在 OOMKilled 后未触发重启策略或处于重启间隙。事实 #4 确认了这一状态在 13 分钟后仍然持续，排除了短暂故障。
2. **现象不符**：虽然日志 #5 和追踪 #6 显示业务请求成功（200 OK），但 Kubernetes 层面容器并未 Ready（Fact #1），这种“能收请求但不被调度/不Ready”的矛盾状态，缺乏明确的 Terminating 证据（如 Terminating Phase 或 Finalizer 阻塞事件）。

## 🎯 根因分析 · g1

### 因果链

```text
容器异常退出(exitCode 137) → 未进入预期重启或Terminating流程 → Pod 卡在 Running+Unready 状态 → 用户观察到 Terminating 矛盾现象（或状态更新滞后）
```

### 根因结论

**证据不足**。
当前工具事实无法确认 Pod 处于 `Terminating` 阶段。相反，Kubernetes 状态（Phase: Running）、Metrics（Restart: 0）以及活跃的 HTTP 流量均指向 Pod 处于 **Running 但 Unready** 的异常状态。exitCode 137 仅为历史残留状态（`last_terminated_reason`），而非当前正在进行的终止动作。由于缺乏 `Terminating` 阶段的关键证据（如 Finalizer 阻塞事件、Killing 状态），无法判定当前现象为 Terminating 阻塞，也无法确定 exitCode 137 是否是导致当前 Unready 状态的直接原因（亦或是应用内部挂死）。需要补充 Container 状态详情（waiting/reason）及 Event 日志以明确“Terminating”指控的真实性及当前僵死的具体机制。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 22.4s
├─ 并发证据采集: 35.2s
│  └─ g1 aiops-case-11/workload: 35.2s (Evidence 24.6s, RCA 10.4s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
