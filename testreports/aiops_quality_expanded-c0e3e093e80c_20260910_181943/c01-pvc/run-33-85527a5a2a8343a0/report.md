## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod aiops-case-v03/workload 处于 Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes (Pod) | `pod.status` = `Pending` (`fact-aa8de59c9570`) | 确认异常现象，Pod 未进入运行阶段 |
| 2 | K8s Event | Kubernetes (Event) | `FailedScheduling`: `persistentvolumeclaim "unavailable-claim" not found` (`fact-1e05a0449090`, `fact-d6b2ce9f280c`) | 定位直接失败原因，调度器无法找到所需的 PVC |
| 3 | Metric | Prometheus (`kube_pod_status_phase`) | `phase: Pending` 值为 `1` (`fact-4889c49976f4`)；`phase: Unknown` 值为 `0` (`fact-48fd81f4aa80`) | 独立确认 Pod 当前仍处于 Pending 状态，未发生隐式状态转换 |

调度器的 `FailedScheduling` 事件明确指出了 PVC 缺失，Metric 进一步证实了 Pod 长期处于该等待状态而未超时转为 Unknown。Pod 的 CPU 和内存资源请求极低（CPU 5m, Memory 8Mi），且没有 Node 资源限制证据，排除了资源不足导致调度的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
PVC 'unavailable-claim' 不存在 → 调度器无法绑定卷资源 → FailedScheduling (PVC not found) → Pod 处于 Pending 状态
```

### 根因结论

已确认根因为**持久卷声明（PVC）缺失**。
Pod `aiops-case-v03/workload` 尝试挂载名为 `unavailable-claim` 的 PVC，但调度器在集群中未能找到该资源。这导致 `default-scheduler` 持续抛出 `FailedScheduling` 事件（证据 #2），使 Pod 被锁定在 `Pending` 状态（证据 #1, #3）。

当前 Kubernetes 事件与状态指标已构成完整的因果闭环，证据充分。由于容器未启动，Logging 和 Tracing 数据不可用，但这对判定此故障无影响。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 37.3s
├─ 并发证据采集: 24.0s
│  └─ g1 aiops-case-v03/workload: 24.0s (Evidence 18.9s, RCA 5.0s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
