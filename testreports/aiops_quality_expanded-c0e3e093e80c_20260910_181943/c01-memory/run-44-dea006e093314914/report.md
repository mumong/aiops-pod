## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod `aiops-case-v02/workload` 的资源请求（Requests）中 Memory 被错误设置为 1Pi（1 Pebibyte），远超集群节点可用容量，导致调度器因 `Insufficient memory` 持续拒绝调度，Pod 处于 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `FailedScheduling  29m (x8 over 64m)  0/3 nodes are available: 3 Insufficient memory.` | 确认调度器因节点内存不足，持续 29 分钟（每 64 分钟重试 8 次）拒绝 Pod 调度 |
| 2 | K8s Config | `container.spec` | `resource_request.memory: "1Pi"` | 暴露 Pod 请求了 1 Pebibyte 内存，远超常规节点容量，为调度失败的根本原因 |
| 3 | K8s Config | `container.spec` | `resource_limit.memory: "1Pi"` | 确认容器硬限制同样被错误设置为 1Pi，加剧了资源不匹配 |
| 4 | Metric | `prometheus` | `kube_pod_status_phase{phase="Pending"} = 1` | 通过监控指标证实 Pod 当前始终处于 Pending 状态 |

**证据说明：**
- Kubernetes 事件直接指出了失败原因（`Insufficient memory`），而配置事实提供了精确的异常数值（`1Pi`），二者结合证实了调度失败的确定性因果。
- Metric 指标从运行时状态维度确认了 Pod 持续滞留于 `Pending` 阶段，与事件中的持续拒绝行为相印证。
- Logging 和 Tracing 数据因容器未启动而无法提供额外信息，但现有的 K8s 事实已足以闭环诊断。

## 🎯 根因分析 · g1

### 因果链

```text
容器 Memory Requests 被错误设置为 1Pi → 调度器在集群中无法找到满足该超大内存需求的节点 → 调度器反复触发 FailedScheduling 事件（Insufficient memory） → Pod 处于 Pending 状态
```

### 根因结论

已确认的根因是 `aiops-case-v02/workload` 的工作负载配置中存在极端的资源请求错误：**Memory Requests 被错误设置为 1Pi（1 Pebibyte）**。

这一配置直接导致集群内所有节点（0/3）因无法满足该内存请求而被调度器排除，引发 `Insufficient memory` 错误。该事实由 `FailedScheduling` 事件（#1）和具体的 `resource_request.memory` 配置值（#2）共同支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 55.7s
├─ 问题定位: 23.3s
├─ 并发证据采集: 24.6s
│  └─ g1 aiops-case-v02/workload: 24.6s (Evidence 19.7s, RCA 4.8s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
