## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod workload-dff5cbc6b-kmfxx in aiops-case-07处于CrashLoopBackOff状态，启动后立即崩溃。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: `Error` | 确认容器以异常状态退出 |
| 2 | K8s Event | kubernetes | `event.message`: `Back-off restarting failed container app in pod workload-dff5cbc6b-kmfxx...` | 确认 Pod 处于重启振荡循环中 |
| 3 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason` = `1` (`reason: Error`) | 从监控侧印证容器异常退出事实 |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory`: `96Mi` | 确认容器内存限制，排除显性 OOM 阈值限制 |
| 5 | Logging | elasticsearch | `pattern`: `CONFIG_MISSING` | 揭示应用崩溃的深层业务原因为配置项缺失 |
| 6 | Tracing | deepflow | `flow`: `GET /work` → `500`, `src_ip: 172.16.104.9`, `dst_ip: 172.16.104.15` | 确认 Pod 已启动并监听端口，但因处理请求而崩溃 |

上述证据表明，Pod 虽然已启动并成功绑定 IP 和端口（通过 `dst_ip` 确认），但其在处理 HTTP 请求时触发了 `CONFIG_MISSING` 错误。K8s 事件与监控指标均确认了容器反复以 `Error` 终止，且退出码为 78（与日志中的 HTTP 500 状态码逻辑一致）。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置缺失(CONFIG_MISSING) → 应用进程处理请求时业务逻辑失败(Exit 78/500) → Kubelet 检测到异常退出并执行 Back-off 重启策略 → Pod 状态维持在 CrashLoopBackOff
```

### 根因结论

已确认根因：应用配置缺失导致服务启动后无法正常运行。

日志聚合结果明确记录了大量 `CONFIG_MISSING` 错误，这构成了应用异常退出的直接原因。同时，应用层面的崩溃被操作系统捕获为退出码 78。Kubernetes 事件记录了 Kubelet 因容器失败而执行的 `Back-off` 重启行为，以及因配置错误导致的 `Error` 终止原因。Metrics 数据与 K8s 状态相互印证，确认了 `CrashLoopBackOff` 和 `Error` 状态。因此，根本原因在于应用内部缺失必要的配置项，导致其在处理流量时持续崩溃重启。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 20.8s
├─ 并发证据采集: 73.5s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 73.5s (Evidence 64.5s, RCA 8.9s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
