## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod被请求终止并设置了较长的terminationGracePeriodSeconds(3900s)，应用主循环与preStop生命周期钩子均阻塞等待'/state/teardown-requested'文件存在，由于该文件尚未出现，Pod停留在Terminating状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.status`: Terminating, 持续时间 `<invalid>` | 确认 Pod 当前停留在终止状态，无法正常释放。 |
| 2 | K8s Config | Kubernetes | `container.app.resource_request.cpu`: 5m, `resource_limit.cpu`: 50m | 资源请求极低，排除因 CPU 资源争抢导致的性能问题。 |
| 3 | K8s Event | Kubernetes | `Killing`, message: `Stopping container app` (48s前) | 确认系统已发起终止请求，开始进入清理流程。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 0 (app容器) | 证实无重启发生，Pod 卡在生命周期内而未崩溃或退出。 |
| 5 | Logging | Elasticsearch | `application started` (2026-09-14T05:27:31.505Z) | 确认应用正常启动，非启动失败类问题。 |

**证据分析：**
*   **状态印证**：K8s State 与 Event 共同确认了 Pod 被 Kubernetes 主动终止的过程，但 Metric 的 `restart_count=0` 和 State 的 `Terminating` 状态说明该终止过程发生了“死锁”（未进入 Completed 或 Failed）。
*   **逻辑排查**：Metric 排除了重启导致的循环，Logging 排除了启动失败。结合事实中描述的 `preStop` 钩子与主循环阻塞现象，确认是应用层面的清理机制未能及时响应退出信号。

## 🎯 根因分析 · g1

### 因果链

```text
Pod被请求终止 → 应用主循环与preStop阻塞等待'/state/teardown-requested'文件 → 文件未出现导致超时 → Pod长期停留在Terminating状态(持续<invalid>)
```

### 根因结论

根因为**应用退出逻辑阻塞**。具体表现为 Pod 设置较长的 `terminationGracePeriodSeconds(3900s)`，但应用主循环与 `preStop` 生命周期钩子均阻塞等待 `/state/teardown-requested` 文件存在，而该文件始终未出现。这导致 Pod 无法正常完成清理并释放资源，长期滞留于 Terminating 状态。现有证据充分支持该结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.6s
├─ 并发证据采集: 47.1s
│  └─ g1 aiops-case-v12/workload: 47.1s (Evidence 40.1s, RCA 6.9s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
