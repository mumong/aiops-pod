## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod spec 中引用的 Secret 'unavailable-input' 不存在，且 volume 未配置为可选 (Optional: false)，导致 kubelet 挂载卷失败，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount`: MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found | 直接揭示 Pod `app` 容器无法启动的根因 |
| 2 | K8s Config | kubernetes | volumeMount `input` 指向 Secret `unavailable-input` | 说明 Secret 引用来源与卷绑定关系 |
| 3 | K8s State | kubernetes | Pod `phase: Pending`, `status: ContainerCreating` | 确认 Pod 停留在启动前阻塞状态 |
| 4 | K8s State | kubernetes | Pod `ContainersReady: False`, reason `ContainersNotReady` | 佐证容器未进入 Running 状态 |
| 5 | K8s Event | kubernetes | `FailedMount` 事件连续触发 (x27 over 64m, x40 over 66m) | 确认挂载失败是持续且未被缓解的系统性故障 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 `1` (reason: `ContainerCreating`) | 从指标维度独立确认容器处于等待挂载状态 |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total` 值为 `0` | 排除容器因 OOM 或 CrashLoopBackOff 导致的崩溃重启问题 |

**证据关联分析：**
K8s Event（事实 #1）明确指出 `Secret 'unavailable-input'` 缺失是导致 `FailedMount` 的唯一原因；K8s State（事实 #3, #4）和 Metric（事实 #6）共同证实了 Pod 由于该挂载错误被阻塞在 `Pending/ContainerCreating` 阶段，且 `restart_count=0`（事实 #7）排除了应用层面的运行时崩溃，将问题严格锁定在基础设施卷挂载阶段。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'unavailable-input' 在集群中不存在 → 容器运行时无法挂载 'input' volume (Optional: false) → kubelet 报 FailedMount 错误并持续重试 → Pod 状态卡在 Pending/ContainerCreating，用户侧容器未启动
```

### 根因结论

**已确认的根因**：Pod `aiops-case-v04/workload` 的 Spec 中配置了非可选卷 (`Optional: false`) 挂载 Secret `unavailable-input`，但该 Secret 在当前命名空间 `aiops-case-v04` 中实际不存在。

该事实由 K8s Event 提供的明确错误原文 `secret "unavailable-input" not found` 直接证实，并由 K8s 状态（Pending, ContainerCreating）及 Metric（Waiting reason, restart_count=0）形成证据闭环，确认这是导致容器无法启动的根本原因。

---

## 📊 性能统计

```text
├─ 总耗时: 52.9s
├─ 问题定位: 14.3s
├─ 并发证据采集: 29.1s
│  └─ g1 aiops-case-v04/workload: 29.1s (Evidence 23.6s, RCA 5.4s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed
