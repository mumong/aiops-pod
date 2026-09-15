## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | 应用容器在 SIGTERM 信号处理程序中阻塞于等待并不存在的 '/state/teardown-requested' 文件，且 terminationGracePeriodSeconds (3900s) 时间远长于已流逝时间，导致 Pod 处于 Terminating 状态但未真正退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase: "Running"` (fact-33f209bdd549) | 确认 Pod 未处于预期的 Terminating 退出阶段，仅停留在 Terminating 状态（fact-bb4b16fd72a4）。 |
| 2 | K8s Event | Kubernetes | `Readiness probe failed: ... timed out` (fact-22f432f5bcdf, 49s) | 证明探针在 Pod 开始终止时（49s前）已超时报错，与“SIGTERM 阻塞”现象时间轴吻合。 |
| 3 | Logging | Elasticsearch | `SIGTERM received; waiting` (fact-e4962a6fa5fe, 07:17:56Z) | 确认应用进程在收到 SIGTERM 信号后进入等待状态，未正常退出。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 0` (fact-1d293443b00d) | 验证此前无异常重启，当前状态是由阻塞引起的终止停滞，而非重启循环。 |

证据分析：
Kubernetes 事件与日志在时间上形成了闭环：探针失败与日志记录 `SIGTERM received; waiting` 紧密相邻，结合 `pod.phase: Running` 但状态显示 Terminating 的事实，直接指向应用进程在信号处理程序（Graceful Shutdown）阶段因逻辑阻塞而无法完成退出。

## 🎯 根因分析 · g1

### 因果链

```text
未实现正确的 SIGTERM 处理或阻塞于等待特定文件 (/state/teardown-requested) → 进程无法响应系统终止信号 → 容器未能在 terminationGracePeriodSeconds 限制内正常退出 → Pod 卡在 Terminating 状态
```

### 根因结论

已确认根因为**应用容器在 SIGTERM 信号处理程序中阻塞**。

证据编号 3 日志明确显示收到信号后“等待”而不停止，证据编号 2 探针超时及证据编号 1 的状态不一致均佐证了容器未执行实际退出流程的事实。结合诊断状态，阻塞原因为等待并不存在的 `/state/teardown-requested` 文件，导致 `terminationGracePeriodSeconds`（3900s）超时机制失效，进程长时间滞留于 Terminating 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 27.0s
├─ 并发证据采集: 41.3s
│  └─ g1 aiops-case-v13/workload: 41.3s (Evidence 35.6s, RCA 5.6s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
