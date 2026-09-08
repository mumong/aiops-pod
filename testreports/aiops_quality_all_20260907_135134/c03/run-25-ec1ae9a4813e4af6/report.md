## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-2xgjz 处于 Pending 状态且容器处于 ContainerCreating，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase: Pending`, `pod.status: Pending` | 确认 Pod 处于不可用状态 |
| 2 | K8s Event | kubernetes | `FailedMount`: `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 直接指出根因：ConfigMap 缺失导致挂载失败 |
| 3 | K8s Event | kubernetes | `FailedMount` (x18 over 41m): `timed out waiting for the condition` | 证实问题持续存在，非瞬时网络波动 |
| 4 | K8s State | kubernetes | `container.waiting_reason: ContainerCreating` | 解释为何容器未运行，进而导致 Metric/Logging 无有效数据 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 确认容器处于等待启动状态，与 K8s Event 一致 |

**证据印证说明**：
K8s 事件 (`fact-da3afe4a528c`) 明确记录了 `configmap "unavailable-config" not found` 这一错误，直接解释了 `FailedMount` 的原因。K8s 状态 (`fact-0c0fb945d2d6`) 显示 Pod 为 `Pending`，且容器状态为 `ContainerCreating`，这与 Metric 数据 (`fact-70294b4334a5`) 相互印证。由于容器因挂载失败而卡在启动前阶段，因此无法产生业务日志或 Trace，符合“容器未启动，物理上不会产生应用日志”的限制说明。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 缺失 → volume 'input' 挂载失败 (FailedMount) → Pod 处于 Pending/ContainerCreating 阶段 → 容器 'app' 无法启动
```

### 根因结论

**已确认的根因**：Pod 规格中声明引用了名为 `unavailable-config` 的 ConfigMap 作为 Volume，但该 ConfigMap 在 `aiops-case-03` 命名空间中不存在。由于该 Volume 未标记为 `Optional: true`，kubelet 无法挂载存储卷，导致容器无法启动，Pod 永久处于 `Pending` 状态。

**支持证据**：
*   K8s 事件明确报出 `configmap "unavailable-config" not found` (`fact-da3afe4a528c`)。
*   Pod 状态和 Waiting Reason (`fact-0c0fb945d2d6`, `fact-70294b4334a5`) 证实了容器因挂载问题而未运行。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 25.8s
├─ 并发证据采集: 37.0s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 37.0s (Evidence 29.4s, RCA 7.5s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-volume-mount-failed, pod-sandbox-create-failed
