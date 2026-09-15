## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod workload (aiops-case-v03) 处于 Pending 状态，节点分配为 <none> |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling`: `0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` | **直接失败证据**：调度器明确指示因 PVC 缺失导致调度失败。 |
| 2 | K8s State | kubernetes | `pod.status`: `Pending` | **症状确认**：Pod 状态停滞在调度前阶段，与调度事件一致。 |
| 3 | K8s Config | kubernetes | `container.resource_limit.cpu`: `50m`<br>`container.resource_request.cpu`: `5m` | **环境上下文**：集群存在充足的 CPU 资源预留，排除资源不足导致的调度延迟。 |

现有证据形成完整闭环：调度器日志（事实 1）直接指出了“PersistentVolumeClaim 'unavailable-claim' not found”这一关键错误，Pod 的 Pending 状态（事实 2）是这一调度失败的自然结果，且 CPU 资源充足（事实 3）排除了因资源碎片或竞争导致的误判。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 模板引用了不存在的 PVC 'unavailable-claim' → 调度器无法绑定卷资源并满足调度约束 → default-scheduler 返回 FailedScheduling 警告事件 → Pod 保持 Pending 状态且未调度到任何节点
```

### 根因结论

**已确认的根因**：Pod `workload` 声明依赖的持久卷声明 `unavailable-claim` 在集群中不存在。
该事实由 K8s Event（事实 1）直接证实，调度器明确报错 `persistentvolumeclaim "unavailable-claim" not found`，这是导致 Pod 始终处于 `Pending` 状态（事实 2）且无法被调度到任意节点的唯一直接原因。

---

## 📊 性能统计

```text
├─ 总耗时: 42.0s
├─ 问题定位: 11.9s
├─ 并发证据采集: 23.3s
│  └─ g1 aiops-case-v03/workload: 23.3s (Evidence 17.1s, RCA 6.1s)
└─ 汇总总结: 6.7s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
