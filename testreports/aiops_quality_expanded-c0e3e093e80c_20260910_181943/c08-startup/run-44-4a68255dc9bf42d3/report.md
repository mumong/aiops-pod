## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Container memory limit (64Mi) is lower than the application's startup memory allocation requirement (256Mi), causing the container process to be OOMKilled by the Kernel. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container=app, reason=OOMKilled | 确认进程被内核 Kill |
| 2 | K8s State | kubernetes | container=app, reason=CrashLoopBackOff | 确认持续重启现象 |
| 3 | K8s Event | kubernetes | Warning BackOff restarting failed container app (da351bf0...) (x489 over 106m) | 证明故障已持续 106 分钟 |
| 4 | K8s Config | kubernetes | container=app, container.resource_limit.memory=64Mi | 提供资源硬限制事实 |
| 5 | K8s Config | kubernetes | container=app, container.resource_request.cpu=5m, container.resource_limit.cpu=100m | 提供 CPU 上下文 |
| 6 | K8s Config | kubernetes | container=app, container.resource_request.memory=8Mi | 提供资源请求上下文 |
| 7 | K8s State | kubernetes | container=app, exit_code=137 | 确认进程被信号终止（OOM） |
| 8 | K8s State | kubernetes | ContainersReady=False, reason=ContainersNotReady | 确认 Pod 无法就绪 |
| 9 | K8s Measurement | kubernetes | container=app, restart_count=25 | 确认故障触发频繁 |
| 10 | Metric | prometheus | kube_pod_container_status_last_terminated_reason=OOMKilled, last_timestamp=2026-09-14T11:13:10Z | 确认最后终止原因 |
| 11 | Metric | prometheus | kube_pod_container_status_waiting_reason=CrashLoopBackOff, timestamp=2026-09-14T11:13:10Z | 确认当前处于回退等待状态 |
| 12 | Logging | elasticsearch | log.message=startup allocation 256Mi | 确认启动所需内存量 |

证据 1、7、10 一致确认进程因 OOM 被内核终止。证据 4 明确容器内存上限仅为 64Mi，而证据 12 指出启动分配需 256Mi。这直接导致内存请求（8Mi）与上限（64Mi）均无法满足应用需求，从而引发内核 OOM Kill，进而触发证据 2、3、11 所描述的重启与不可就绪现象。

## 🎯 根因分析 · g1

### 因果链

```text
Container memory limit (64Mi) < startup requirement (256Mi) → Kernel OOMKilled the app process → K8s restart container → Pod CrashLoopBackOff & NotReady
```

### 根因结论

已确认根因为 **容器内存限制配置严重不足**。

证据 4 显示 `memoryLimit` 仅为 `64Mi`，而证据 12 日志明确指出启动分配要求为 `256Mi`。这导致容器在启动时无法分配足够的内存，立即触发内核 OOM Kill（证据 1、7、10），引发持续崩溃重启（证据 2、3、9），表现为 Pod 无法就绪（证据 8、11）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.3s
├─ 并发证据采集: 52.7s
│  └─ g1 aiops-case-v15/workload: 52.7s (Evidence 46.8s, RCA 5.6s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
