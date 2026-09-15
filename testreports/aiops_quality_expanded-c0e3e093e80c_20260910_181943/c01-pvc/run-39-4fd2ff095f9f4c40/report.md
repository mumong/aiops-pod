## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod aiops-case-v03/workload 处于 Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (`fact-2a0e836cede9`) | `FailedScheduling` (49m): `0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found.` | 明确指向调度失败的直接原因是缺失 PVC 资源 |
| 2 | K8s State | kubernetes (`fact-ae182c37c39a`) | `PodScheduled=False`: `reason: Unschedulable`, `message: ... persistentvolumeclaim "unavailable-claim" not found.` | 与 Event 一致，确认为静态未调度状态 |
| 3 | K8s Event | kubernetes (`fact-dd783a13b145`) | `FailedScheduling` (23m): `preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..` | 进一步排除资源抢占因素，确认 PVC 缺失是唯一阻塞点 |
| 4 | K8s Config | kubernetes (`fact-21f6db0d3a21`) | `container.resource_limit.memory`: `32Mi` | 资源限制正常，非因 Pod 资源过大导致无法调度 |
| 5 | Tool Failure | kubectl (`command_failed`) | `Error from server (NotFound): persistentvolumeclaims "unavailable-claim" not found` | 直接证实 PVC 确实不存在于该命名空间中 |

**证据印证：**
调度事件 (证据 1, 3) 与 Pod 状态 (证据 2) 均指向 `persistentvolumeclaim "unavailable-claim" not found`。工具执行结果 (证据 5) 在外部层面验证了该 PVC 确实不存在。资源限制 (证据 4) 正常，排除了其他调度原因。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 声明引用了不存在的 PVC 'unavailable-claim' → 调度器无法绑定所需存储资源 → 触发 FailedScheduling 失败 → Pod 持续处于 Pending (Unschedulable) 状态
```

### 根因结论

已确认的根因为：Pod `aiops-case-v03/workload` 的 YAML 定义中引用了名为 `unavailable-claim` 的持久卷声明（PersistentVolumeClaim），但该资源在命名空间 `aiops-case-v03` 中不存在。调度器因无法获取所需的存储资源而拒绝调度该 Pod。

证据支持：
- K8s 调度事件 (fact-2a0e836cede9, fact-dd783a13b145) 和 Pod 状态 (fact-ae182c37c39a) 直接报告了 `persistentvolumeclaim "unavailable-claim" not found`。
- `kubectl get pvc` 调用失败并返回 `NotFound` 错误 (fact-tool-failed-01)，提供了该 PVC 缺失的确凿证明。
- 资源限制配置正常 (fact-21f6db0d3a21)，且无预emption 可能性 (fact-dd783a13b145)，排除了其他故障原因。

该结论由 K8s 状态和事件事实直接支撑，证据充分，诊断置信度高。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 16.5s
├─ 并发证据采集: 37.5s
│  └─ g1 aiops-case-v03/workload: 37.5s (Evidence 30.2s, RCA 7.2s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
