## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 处于 Pending 状态，被调度器拒绝 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedScheduling ... 0/3 nodes are available: 3 Insufficient memory` | 核心现象：调度器因内存不足拒绝调度该 Pod。 |
| 2 | K8s Config | Kubernetes | `resource_request.memory: 1Pi` (容器 app) | 故障根源：Pod 请求了 1 PiB 的内存资源。 |
| 3 | K8s State | Kubernetes | `pod.status: Pending` | 当前状态：Pod 未分配节点，持续处于 Pending 状态。 |
| 4 | Metric | Prometheus | `kube_pod_status_phase{phase="Pending"}` = 1 (采样数 1) | 辅助确认：指标反映了 Pod 持续处于 Pending 阶段。 |

**证据说明：**
Kubernetes Event (`#1`) 明确记录了调度失败原因与配置 (`#2`) 的直接冲突：请求的资源量 (1 PiB) 超出了集群节点的资源承载能力，导致 Pod 状态长期维持为 Pending (`#3`)。Metric 数据 (`#4`) 从监控维度佐证了 Pod 未能进入 Running 状态的事实。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 1 PiB (1125899906842624 bytes) 的 memory request → 集群节点最大可用内存无法满足该资源请求 → Default Scheduler 报告 0/3 nodes are available: 3 Insufficient memory → Pod 持续处于 Pending 状态且无法调度
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-v02/workload` 的配置文件错误地指定了极高的内存请求量（`1Pi`，即 1 PiB）。由于该资源量远超集群任意节点的可分配内存上限，导致 Kubernetes 调度器 (default-scheduler) 在尝试绑定 Pod 时均因 `Insufficient memory` 失败 (`#1, #2`)。这直接导致 Pod 无法被分配到任何节点，从而一直保持在 `Pending` 状态 (`#3`)。

---

## 📊 性能统计

```text
├─ 总耗时: 49.8s
├─ 问题定位: 14.8s
├─ 并发证据采集: 27.7s
│  └─ g1 aiops-case-v02/workload: 27.7s (Evidence 20.6s, RCA 7.0s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
