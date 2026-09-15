## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod aiops-case-v03/workload 处于 Pending 状态，因调度器无法绑定 Volume 而持续 FailedScheduling。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod aiops-case-v03/workload 状态为 Pending (fact-080629abdb8a) | 确认 Pod 处于停滞状态，未进入运行期 |
| 2 | K8s Event | kubernetes | FailedScheduling: 0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found. (fact-0e64ac1171c1, fact-8359a2477df3) | 直接证据：调度器因找不到 PVC 而无法分配节点，明确指向 Volume 绑定失败 |
| 3 | Metric | prometheus | kube_pod_status_phase 在 phase=Pendding 下值为 1 (fact-f57144f9c383) | 确认当前无运行中的 Pod 样本，与 K8s State 状态一致 |
| 4 | K8s Config | kubernetes | container app 请求 CPU 5m / 32Mi，限制 CPU 50m / 32Mi (fact-9d9154b7b3fa, fact-a799cbaf26b7) | 资源规格极小，排除资源不足导致 Pending 的可能 |
| 5 | Topology | kubernetes | PVC 'unavailable-claim' 在 namespace aiops-case-v03 下未找到 (kubectl_get_by_name 返回 NotFound, fact-42ccdfeea1b4) | 确认 Pod spec 中引用的依赖资源确实不存在 |

**证据说明：**
Kubernetes 事件 (fact-0e64ac1171c1) 提供了最直接的失败原因：调度器尝试绑定时，发现 Pod spec 中引用的 `unavailable-claim` PVC 不存在。Pod 状态 (fact-080629abdb8a) 和 Prometheus 指标 (fact-f57144f9c383) 均确认了 Pod 持续处于 Pending 阶段。由于容器尚未启动，Logging 和 Tracing 维度无数据。资源规格 (fact-9d9154b7b3fa) 显示请求量极低，排除了节点资源耗尽导致调度失败的可能。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 引用了不存在的 PVC 'unavailable-claim' → 调度器执行绑定时发现 PVC NotFound，无法满足 Volume 调度约束 → 调度器返回 FailedScheduling 事件，标记 0/3 节点可用 → Pod 持续保持 Pending 状态
```

### 根因结论

已确认的根因是：Pod `aiops-case-v03/workload` 的 spec 定义中引用的 PersistentVolumeClaim 'unavailable-claim' 在 namespace `aiops-case-v03` 中不存在。这导致 Kubernetes 调度器在执行绑定（Binding）操作时，无法找到对应的 Volume 资源，从而触发 `FailedScheduling` 事件，使 Pod 一直停留在 Pending 状态。

**引用证据：**
- 调度器明确的 NotFound 报错 (fact-0e64ac1171c1)
- PVC 实际查询结果为空 (fact-42ccdfeea1b4)

**未确认项：**
- PVC 'unavailable-claim' 是被误删、从未创建还是在其他 namespace？
- Pod 是否由未暴露的控制器创建，导致无法自动修正 spec？

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 13.8s
├─ 并发证据采集: 36.5s
│  └─ g1 aiops-case-v03/workload: 36.5s (Evidence 27.7s, RCA 8.7s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
