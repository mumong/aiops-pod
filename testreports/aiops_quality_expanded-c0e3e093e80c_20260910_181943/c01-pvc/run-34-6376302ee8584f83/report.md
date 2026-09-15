## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod 定义中引用了不存在的 PersistentVolumeClaim 'unavailable-claim'，导致调度器无法满足存储卷挂载约束，持续返回 FailedScheduling 事件。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | event.message | `Warning FailedScheduling 9m46s (x5 over 29m) default-scheduler 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found...` | 确保持续的调度失败与 PVC 缺失直接相关 |
| 2 | K8s State | pod.condition | `type: PodScheduled, status: False, reason: Unschedulable, message: 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found...` | 提供 Pod 处于阻塞状态的确切条件原因 |
| 3 | K8s State | pod.phase | `Pending` | 确认应用运行状态为挂起 |
| 4 | K8s Config | container.resource_request.cpu | `5m` | 排除 CPU 资源不足导致调度的可能 |
| 5 | K8s Config | container.resource_limit.memory | `32Mi` | 排除内存限制导致调度的可能 |
| 6 | Metric | kube_pod_status_phase | `1` (pending phase) / `0` (succeeded phase) | 确认 Pod 长期处于 Pending 状态且未进入 Succeeded 阶段 |

**证据印证说明：**
K8s Event 与 K8s State 中的 `message` 字段精确匹配，一致指出核心阻碍是 `persistentvolumeclaim "unavailable-claim" not found`。配置类证据（Fact 4, 5）显示资源请求极低，排除了资源短缺。Metric 证据（Fact 6）证实了该异常状态在观测窗口内的持续性。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 定义引用不存在的 PVC 'unavailable-claim' → 调度器无法满足存储卷挂载约束 → 持续触发 FailedScheduling 事件并拒绝调度 → Pod 长期处于 Pending 状态
```

### 根因结论
已确认的根因：Pod 定义中引用了不存在的 PersistentVolumeClaim `'unavailable-claim'`。
这一缺失导致 K8s 调度器无法找到满足持久化卷挂载要求的节点（见事实 #1, #2），从而阻断调度流程，引发 Pod 持续停留在 Pending 状态（见事实 #3, #6）。证据链完整，根因明确。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 23.0s
├─ 并发证据采集: 37.4s
│  └─ g1 aiops-case-v03/workload: 37.4s (Evidence 33.0s, RCA 4.3s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
