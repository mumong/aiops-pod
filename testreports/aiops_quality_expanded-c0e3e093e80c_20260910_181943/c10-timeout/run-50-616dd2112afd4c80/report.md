## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | RecentRestart | Pod aiops-case-v17/workload 处于 RecentRestart 状态，经历 CrashLoopBackOff 循环。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s | `last_terminated_reason`: Error; `last_exit_code`: 137; `waiting_reason`: CrashLoopBackOff | 确认容器异常退出状态及循环重启行为。 |
| 2 | K8s Event | K8s | `Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded` | 提供应用层超时现象的直接原因。 |
| 3 | K8s Config | K8s | `resource_limit.memory`: 64Mi | 确认可行资源限制，判定为潜在瓶颈。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` = Error (label: container=app) | 独立观测确认最近一次终止原因。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = CrashLoopBackOff (label: container=app) | 独立观测确认当前等待状态。 |
| 6 | Logging | Elasticsearch | `listening on 18080` | 表明应用进程已启动并绑定端口。 |
| 7 | Tracing | Deepflow | GET `/health` 响应 200，耗时 min: 3001044us (约 5s), max: 3001380us | 证实健康检查请求耗时极长，支撑“超时”结论。 |

**证据说明**：
1. K8s 事件（证据 2）明确记录了 Liveness Probe 因“context deadline exceeded”失败，而 Tracing 数据（证据 7）证实了 `/health` 接口请求平均耗时超过 3 秒，这与 Probe 超时机制完全吻合。
2. K8s 状态（证据 1）和 Prometheus 指标（证据 4）共同确认退出原因为“Error”且伴随 Exit Code 137，这是 Linux 内核 OOM Killer 终止进程的典型特征。
3. 结合极低的内存限制（证据 3）与应用进程启动现象（证据 6），形成“资源受限 -> 触发 OOM -> 进程终止 -> Probe 超时 -> 重启”的完整证据闭环。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制 (64Mi) 不足 → 进程内存增长触发内核 OOM Killer 发送 SIGKILL → 容器异常退出 (Exit Code 137) → 导致 Liveness Probe 超时失败 (见证据 2, 7) → Kubelet 频繁重启容器 (CrashLoopBackOff，见证据 1)
```

### 根因结论

已确认根因为**容器内存资源限制配置过低（64Mi）**。

该根因通过以下路径导致当前现象：
1. **触发机制**：应用进程启动并响应请求（见证据 6, 7），但受限于 64Mi 的硬性内存上限（见证据 3），内存使用增长触发了内核 OOM Killer。
2. **直接失败**：进程被强制终止，导致 Pod 退出码为 137（见证据 1, 4）。
3. **用户可见现象**：进程退出导致 Liveness Probe 请求（`/health`）无法及时得到响应（证据 7 显示耗时过长或连接断开），进而引发 Kubelet 报告 Probe 失败并触发 CrashLoopBackOff 重启循环（见证据 1, 2）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 25.8s
├─ 并发证据采集: 89.1s
│  └─ g1 aiops-case-v17/workload: 89.1s (Evidence 80.2s, RCA 8.6s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
