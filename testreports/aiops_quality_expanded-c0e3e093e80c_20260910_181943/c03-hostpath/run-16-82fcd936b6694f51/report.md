## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod workload (aiops-case-v06) stuck in ContainerCreating/Pending state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount`: hostPath type check failed: `/var/lib/aiops-fixture-unavailable-7f394bef/input` is not a directory (over 19m, x17) | **核心原因**：直接指出宿主机路径类型不匹配，导致挂载失败。 |
| 2 | K8s Event | kubernetes | `FailedMount`: unable to attach or mount volumes: unmounted volumes=[input] (over 16m, x8) | **核心原因佐证**：持续确认挂载卷状态异常。 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 中 `reason=ContainerCreating` 的值为 1 | **现象印证**：确认容器处于等待挂载的特定状态。 |
| 4 | Metric | prometheus | `kube_pod_status_phase` 中 `phase=Pending` 的值为 1 | **现象印证**：确认 Pod 处于 Pending 阶段。 |

**证据说明：**
K8s Event 明确报告了 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 路径类型检查失败的错误，这直接解释了 Metric 中观测到的 `ContainerCreating` 和 `Pending` 状态。由于容器无法启动，Logging 与 Tracing 维度为 `not_applicable`，所有证据均指向挂载配置与宿主机文件系统状态的冲突。

## 🎯 根因分析 · g1

### 因果链

```text
node2 宿主机路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 类型非目录 (事实 1) → kubelet 执行 hostPath 类型检查失败，无法挂载输入卷 → 挂载卷状态持续异常 (事实 2) → Pod 无限期停留在 ContainerCreating/Pending 状态 (事实 3, 4)
```

### 根因结论

已确认根因为 **`/var/lib/aiops-fixture-unavailable-7f394bef/input` 路径类型不匹配**（事实 1）。该路径在宿主机上可能是一个文件、管道或完全不存在，导致 kubelet 无法将其作为目录挂载到 Pod 中。这一物理状态的冲突直接造成了 Pod 永远无法完成挂载步骤，进而无法启动应用容器。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 48.8s
├─ 并发证据采集: 40.0s
│  └─ g1 aiops-case-v06/workload: 40.0s (Evidence 30.7s, RCA 9.3s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed, pod-volume-mount-failed
