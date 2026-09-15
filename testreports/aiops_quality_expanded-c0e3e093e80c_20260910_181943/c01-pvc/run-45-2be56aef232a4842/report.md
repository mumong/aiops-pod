## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod `aiops-case-v03/workload` 的 YAML 配置中声明挂载名为 `unavailable-claim` 的 PersistentVolumeClaim (PVC)，但该 PVC 在命名空间中不存在。调度器因无法绑定该缺失的存储卷而持续拒绝调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase`: Pending | 确认 Pod 当前处于挂起状态，未进入运行阶段 |
| 2 | K8s Event | Kubernetes | `FailedScheduling`: `persistentvolumeclaim "unavailable-claim" not found` | 直接指出调度失败的原因为找不到指定的 PVC |
| 3 | K8s Config | Kubernetes | `PVC` 挂载目标: `unavailable-claim` | 提供故障的具体实体标识符，确认引用了不存在的资源 |
| 4 | K8s State | Kubernetes | `pod.condition`: `Unschedulable` (message 同上) | 与 Event 事件相互印证，证实调度器判定不可调度 |
| 5 | Metric | Prometheus | `kube_pod_status_phase` (phase=Pending): 1 | 监控数据确认 Pod 持续处于 Pending 状态 |

**证据关联说明**：Kubernetes 配置事实（#3）揭示了 Pod 声明了不存在的 PVC `unavailable-claim`，这一配置缺陷直接触发了调度器的校验逻辑，导致 K8s Event（#2）与 Condition 状态（#4）一致报错 `not found`，进而使 Pod 长期保持 Pending 状态并被 Metric 监控捕获（#5）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了不存在的 PVC (`unavailable-claim`) → 调度器校验卷绑定时发现目标 PVC 缺失 → 触发 `persistentvolumeclaim not found` 错误导致调度判定 Unschedulable → Pod 持续处于 Pending 状态
```

### 根因结论

已确认根因为 **Pod 配置引用了不存在的 PersistentVolumeClaim (`unavailable-claim`)**。调度器在尝试调度 Pod 时，无法找到 YAML 中声明挂载的 PVC 资源，直接拒绝调度。此结论由 K8s 配置事实、调度事件及 Pod 状态事实相互印证（证据编号：1-5）。

---

## 📊 性能统计

```text
├─ 总耗时: 52.5s
├─ 问题定位: 12.2s
├─ 并发证据采集: 33.3s
│  └─ g1 aiops-case-v03/workload: 33.3s (Evidence 23.8s, RCA 9.5s)
└─ 汇总总结: 6.9s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
