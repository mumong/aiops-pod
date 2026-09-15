## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod 请求的 memory limit (1Pi) 远超集群节点可用内存，导致 default-scheduler 因 Insufficient memory 无法调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | K8s | `resource_request.memory`: 1Pi | 定义异常请求量 |
| 2 | K8s Config | K8s | `resource_limit.memory`: 1Pi | 定义异常硬限制 |
| 3 | K8s State | K8s | `pod.status`: Pending | 展示最终异常现象 |
| 4 | K8s Event | K8s | `reason`: FailedScheduling, `message`: 0/3 nodes are available: 3 Insufficient memory | 直接诊断调度失败原因 |

- **K8s 维度**：事件与状态互为印证，Pod 因 1Pi 的内存请求导致 scheduler 在 3 个节点上均因内存不足而调度失败。
- **Logging/Tracing 维度**：Pod 处于 Pending 状态，无法启动容器，因此不存在应用日志或 Trace 数据，与预期一致。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置 1Pi 内存请求 → 集群无足够节点资源 → Scheduler 触发 Insufficient memory → Pod 处于 Pending 状态
```

### 根因结论

- **已确认的根因**：Pod (`aiops-case-v02/workload`) 配置了 `1Pi` 的内存请求与限制（证据 1、2），该资源量远超集群中所有节点（共 3 个）的可用内存（证据 4），导致 `default-scheduler` 拒绝调度（证据 4），进而使 Pod 长期处于 `Pending` 状态（证据 3）。
- **证据评估**：Kubernetes 事件（证据 4）已直接给出 `Insufficient memory` 结论，且 Pod 状态（证据 3）与配置（证据 1、2）逻辑自洽，无需补充 Metric 或 Log 即可确诊。

---

## 📊 性能统计

```text
├─ 总耗时: 59.8s
├─ 问题定位: 22.6s
├─ 并发证据采集: 30.6s
│  └─ g1 aiops-case-v02/workload: 30.6s (Evidence 23.3s, RCA 7.2s)
└─ 汇总总结: 6.6s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
