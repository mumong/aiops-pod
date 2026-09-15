## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod aiops-case-v04/workload stuck in Pending/ContainerCreating state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount`: MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found (23 occurrences over 36m) | 直接证据，表明挂载失败的具体原因是 Secret 缺失 |
| 2 | K8s State | kubernetes | `Pod status: Pending` | 当前异常状态，与 K8s Event 描述的挂载受阻阶段一致 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason: ContainerCreating) | 确认容器处于等待阶段，且无重启记录（restarts_total: 0） |

上述证据链一致：容器因依赖的 Secret `unavailable-input` 不存在，导致 kubelet 挂载卷失败，从而使 Pod 持续卡在 Pending/ContainerCreating 状态。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'unavailable-input' 不存在 → kubelet MountVolume.SetUp 失败 → Pod 持续处于 Pending 状态 → 无法启动
```

### 根因结论

已确认的根因是 Pod 引用的 Secret `unavailable-input` 在命名空间 `aiops-case-v04` 中缺失。Kubernetes Event 中反复记录的 `FailedMount` 错误明确指出了该 Secret 不存在是导致挂载失败（`MountVolume.SetUp failed`）的直接原因，进而导致 Pod 无法从 `Pending` 状态转换为 `Running`。

---

## 📊 性能统计

```text
├─ 总耗时: 58.2s
├─ 问题定位: 20.1s
├─ 并发证据采集: 32.8s
│  └─ g1 aiops-case-v04/workload: 32.8s (Evidence 24.5s, RCA 8.2s)
└─ 汇总总结: 5.4s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-imagepull-failed
