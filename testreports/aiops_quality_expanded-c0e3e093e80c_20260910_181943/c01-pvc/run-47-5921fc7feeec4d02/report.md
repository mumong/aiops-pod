## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod aiops-case-v03/workload 处于 Pending 状态且无法调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` (state) | `pod.status` = `Pending` | 确认 Pod 处于未调度状态的核心症状 |
| 2 | K8s Event | `kubernetes` (event) | `FailedScheduling`: `0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found` | 直接指出调度失败的根因为 PVC 找不到 |
| 3 | K8s Config | `kubernetes` (config) | `container.resource_request.memory` = `8Mi` | 证明 Pod 资源请求量极小，非资源不足导致 |
| 4 | K8s Config | `kubernetes` (config) | `container.resource_request.cpu` = `5m` | 证明 Pod 资源请求量极小，非资源不足导致 |
| 5 | Metric | `prometheus` | `kube_pod_status_phase` (Pending) 值为 `1` | 从监控维度独立确认 Pod 持续处于 Pending 阶段 |
| 6 | Metric | `prometheus` | `kube_pod_status_phase` (Succeeded) 值为 `0` | 排除 Pod 已成功完成或退出的可能性 |

**证据关联说明**：
K8s 事件 (证据 #2) 明确给出了 `FailedScheduling` 的原因是 `persistentvolumeclaim "unavailable-claim" not found`。这一结论被 Pod 的 `Pending` 状态 (证据 #1) 和对应的 Prometheus 指标 (证据 #5) 交叉印证。资源配置 (证据 #3, #4) 极低，排除了因资源争抢或节点资源不足导致的调度失败，进一步锁定为声明式资源不存在的问题。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了不存在的 PVC 'unavailable-claim' → Scheduler 无法绑定 PV/PVC 且找不到可用节点 → 持续触发 FailedScheduling 事件 → Pod 卡在 Pending 状态
```

### 根因结论

**已确认根因**：Pod 在定义中引用了一个名为 `unavailable-claim` 的 PersistentVolumeClaim，但该 PVC 在当前命名空间不存在。

*   **支撑证据**：Kubernetes 调度器事件 (`fact-1b9d867823bc`, `fact-c56609ee991e`) 一致报告 `persistentvolumeclaim "unavailable-claim" not found`。这是导致 `FailedScheduling` 且 Pod 无法进入 `Running` 状态的直接原因。
*   **排除项**：资源请求值 (`8Mi` 内存, `5m` CPU) 极低，排除了资源容量不足；监控指标确认了状态持续为 Pending，排除了偶发性或瞬时故障。

**未决问题**：虽然确定是 PVC 不存在导致调度失败，但 PVC 缺失的根本原因（是配置笔误、上游资源未创建，还是命名空间不匹配）在当前事实中未完全明确，需进一步核查 PVC 定义或上游依赖。

---

## 📊 性能统计

```text
├─ 总耗时: 59.0s
├─ 问题定位: 21.1s
├─ 并发证据采集: 27.9s
│  └─ g1 aiops-case-v03/workload: 27.9s (Evidence 21.1s, RCA 6.7s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
