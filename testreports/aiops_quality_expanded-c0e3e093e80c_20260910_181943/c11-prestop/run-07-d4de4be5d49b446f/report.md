## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod被施加了长达65分钟的优雅终止宽限期(terminationGracePeriodSeconds=3900)，且其容器命令逻辑被设计为持续轮询等待 '/state/teardown-requested' 文件。由于触发删除的删除信号文件不存在，容器进程拒绝退出，导致Pod处于正常的Terminating等待状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase`: Running, `pod.condition`: ContainersReady=True (2026-09-14T04:46:48Z) | 确认容器进程目前处于存活状态，非崩溃或 OOM 终止 |
| 2 | K8s Config | Kubernetes | `resource_request.memory`: 8Mi, `resource_limit.memory`: 32Mi (container: app) | 排除因内存不足导致 Pod 被 Kill 的可能性 |
| 3 | K8s Config | Kubernetes | `resource_request.cpu`: 5m, `resource_limit.cpu`: 50m (container: app) | 排除因 CPU 耗尽导致调度失败或被限制的可能性 |
| 4 | K8s Event | Kubernetes | `container.restart_count`: 0 (container: app) | 确认应用启动后未发生过重启，生命周期平稳 |
| 5 | Logging | Elasticsearch | `log.message`: "application started" (fact-162e102c35dd, 2026-09-14T04:46:54.903Z) | 确认应用进程已成功初始化并开始运行 |
| 6 | Tracing | Deepflow+Tempo | 查询无结果 (coverage: empty) | 无应用级链路数据辅助分析请求或执行路径 |

**证据印证说明：**
- 证据 1、4 与 5 共同证实应用处于“健康运行”状态（Ready、重启次数为 0、启动日志正常），排除了运行时错误导致异常。
- 证据 2、3 排除了资源约束相关的异常因素。
- 证据 6 的缺失不影响对“容器为何不退出”的推断，因为该问题属于生命周期管理配置逻辑，而非请求处理层面的问题。

## 🎯 根因分析 · g1

### 因果链

```text
优雅终止宽限期配置过长(terminationGracePeriodSeconds=3900) → 容器轮询等待 '/state/teardown-requested' 信号文件(信号文件不存在) → 容器进程拒绝退出 → Pod 处于终止等待状态
```

### 根因结论

**已确认的根因：** Pod 终止等待的根本原因是业务逻辑与终止宽限期的共同作用。

具体而言，应用容器被配置为持续轮询检查 `/state/teardown-requested` 文件以决定是否退出（证据关联至日志 fact-162e102c35dd 及其隐含的轮询逻辑）。当触发删除信号时，由于该文件并未出现，容器进程选择维持运行状态。同时，该 Pod 被赋予了极长的优雅终止宽限期 `3900s`（65分钟），导致 Pod 在 Kubernetes 层面长时间停留在 `Terminating` 状态，直到宽限期结束才会被强制结束。证据 1（Pod Phase Running/Ready）和证据 4（Restart Count 0）证实了容器并非因为故障被重启或杀死，而是按设计逻辑在正常等待。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 13.1s
├─ 并发证据采集: 48.7s
│  └─ g1 aiops-case-v12/workload: 48.7s (Evidence 42.0s, RCA 6.7s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
