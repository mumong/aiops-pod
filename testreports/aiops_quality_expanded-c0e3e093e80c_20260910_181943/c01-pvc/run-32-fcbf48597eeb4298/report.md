## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod aiops-case-v03/workload 处于 Pending 状态，未绑定节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `FailedScheduling ... 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.` (事实 ID: fact-979112bc1a3a) | 确认调度器因缺少 PVC 而无法完成调度，直接阻碍 Pod 运行。 |
| 2 | K8s Config | `aiops-case-v03/workload` (Pod Spec) | 容器 `app` 请求 CPU: `5m`, 内存: `8Mi`; 限制 CPU: `50m`, 内存: `32Mi` (事实 ID: fact-3384941008da, fact-35b1784b72fb) | 确认 Pod 资源声明符合调度逻辑，资源配额不是导致 Pending 的原因。 |
| 3 | K8s State | `aiops-case-v03/workload` | `PodScheduled` condition status: `False`, reason: `Unschedulable`, message: `0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.` (事实 ID: fact-593d058b7a80) | 从 Pod 状态层面印证调度器返回的失败机制及根本原因。 |

**证据分析：**
Kubernetes 事件与 Pod 状态的条件描述高度一致，共同指向 PVC "unavailable-claim" 缺失这一单一瓶颈。资源请求和限制配置处于极低且合理的水平，排除了资源竞争因素。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义中包含 volumes 声明引用 PVC 'unavailable-claim' (事实 2) 
→ 调度器在命名空间 aiops-case-v03 中查找该 PVC 失败 (事实 1) 
→ default-scheduler 判定 0/3 nodes available，Pod 保持 Pending 状态 (事实 3)
```

### 根因结论

已确认根因为 **声明挂载的 PersistentVolumeClaim "unavailable-claim" 在当前命名空间（aiops-case-v03）中不存在**。

该缺失的 PVC 导致 `default-scheduler` 在预调度阶段即无法通过卷依赖检查，进而将 Pod 标记为 `Unschedulable` 并持续处于 `Pending` 状态。此结论已由调度器返回的 `FailedScheduling` 事件（事实 1）及 Pod 的 `Unschedulable` 条件状态（事实 3）双重印证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 17.1s
├─ 并发证据采集: 36.6s
│  └─ g1 aiops-case-v03/workload: 36.6s (Evidence 29.0s, RCA 7.5s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
