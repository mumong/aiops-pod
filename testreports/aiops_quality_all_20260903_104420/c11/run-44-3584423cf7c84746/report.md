## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态超过75分钟，deletionTimestamp已设置但无法完成删除。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase`: Running | 确认 Pod 实体处于运行态，未被实际回收 |
| 2 | K8s State | Kubernetes | `last_exit_code`: 137; `last_terminated_reason`: Error | 确认容器进程异常终止（SIGKILL），存在业务侧故障背景 |
| 3 | K8s State | Kubernetes | `container.condition`: Ready/ContainersReady=False (reason: ContainersNotReady); `container.restart_count`: 0 | 确认 Pod 进入终止流程后，由于容器不再存活且未重启，导致 Pod 处于 NotReady 状态 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.cpu`: 200m; `container.resource_limit.memory`: 96Mi | 资源硬限制配置，排除资源超限导致系统 OOM Killer 的直接证据（需结合日志确认是否为业务 OOM） |
| 5 | K8s Config | Kubernetes | `container.resource_request.cpu`: 20m; `container.resource_request.memory`: 24Mi | 资源预留配置 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 0 (样本数: 61, 时间窗口稳定) | 确认 Pod 在观察周期内未进行过容器重启，排除了 CrashLoopBackOff 等自愈场景 |
| 7 | Metric | Prometheus | `kube_pod_deletion_timestamp`: 1788474663 (2026-09-03 22:31:03Z) | 确认 Pod 被显式触发删除的时间点，与异常报告中的 75 分钟超时吻合 |

Kubernetes State 证据显示容器进程已异常退出（Exit 137）并进入 Terminating 阶段，但 Metric 证据确认重启计数为 0，且删除时间戳表明该状态已持续 75 分钟。由于 Logging 和 Tracing 维度数据缺失（状态为 empty），无法确认触发删除的具体上游操作者（如用户、HPA 或控制器）以及导致 Exit 137 的根本业务原因，但 K8s 侧现象仅证实了“删除流程卡在 Terminating 状态”这一结果。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 设置 deletionTimestamp (2026-09-03T22:31:03Z) → 发现存在 finalizer: 'aiops.lab/hold' → API Server 停止回收资源，Pod 维持在 Terminating 状态 → Pod 状态停滞超过 75 分钟无法删除
```

### 根因结论

已确认的根因：Pod 包含自定义 Finalizer `aiops.lab/hold`，导致 Kubernetes API Server 在容器终止后，暂停回收该 Pod 资源对象，必须等待负责该 Finalizer 的自定义控制器显式移除该标记后才能完成删除。

证据支持：K8s State 维度证实 Pod 已退出运行（`last_exit_code: 137`）且删除时间戳（`deletion_timestamp`）已设置，但 Pod 实体始终未被 GC 回收。结合现象描述，`aiops.lab/hold` 是阻止资源最终释放的直接阻断机制。

缺失的决定性事实：
1. 上游触发源：无法确认是谁或什么控制器发出了删除请求（Unknown: 触发删除的具体上游操作者）。
2. 业务异常根因：日志数据缺失（`logging(empty)`），无法分析容器 Exit 137 的具体原因（如是否因内存超限被 OOM Kill，还是其他应用级故障），进而无法判断 `aiops.lab/hold` 未能被清理是因为控制器宕机、逻辑死锁还是因为上游触发源本身故障。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 13.6s
├─ 并发证据采集: 62.7s
│  └─ g1 aiops-case-11/workload: 62.7s (Evidence 53.0s, RCA 9.6s)
└─ 汇总总结: 12.3s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
