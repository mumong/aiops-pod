## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod workload in aiops-case-v04 is stuck in ContainerCreating/Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-b391759b75da` | `FailedMount: MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` | 直接指出因缺失 Secret 导致卷挂载失败 |
| 2 | K8s Event | `fact-257da96e7555` | `Unable to attach or mount volumes: unmounted volumes=[input]... timed out waiting for the condition` | 证实挂载超时，与上述失败原因一致 |
| 3 | K8s State | `fact-05c69cddcb72` | `phase: Pending` | 证实 Pod 因挂载问题卡在启动前状态 |
| 4 | K8s State | `fact-b6c97b35ce85` | `container.waiting_reason: ContainerCreating` | 证实容器无法进入运行状态 |
| 5 | K8s Config | `fact-259493646559` | `container.resource_limit.memory: 32Mi` | 提供资源上下文（限制非根因） |
| 6 | K8s Config | `fact-2513db05b338` | `container.restart_count: 0` | 证实因挂载未通过，容器从未启动，故无重启 |
| 7 | Metric | `fact-1506ee33f821` | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 独立验证了 Pod 处于等待状态的事实 |

**证据印证：**
Kubernetes 事件 `fact-b391759b75da` 明确指出缺失的 Secret `unavailable-input` 是导致挂载失败的根本原因。该原因直接解释了为何 Pod 处于 `Pending` 状态（`fact-05c69cddcb72`）、容器无法启动（`fact-b6c97b35ce85`），进而导致重启次数为 0（`fact-2513db05b338`）且 Metric 显示为 `ContainerCreating`（`fact-1506ee33f821`）。所有状态与指标均一致指向卷挂载配置错误。

## 🎯 根因分析 · g1

### 因果链

```text
Namespace 中不存在 Secret 'unavailable-input' → Pod 卷 'input' 挂载失败（Optional=false） → Kubelet 报 FailedMount 错误并超时 → Pod 卡在 Pending/ContainerCreating 状态
```

### 根因结论

**已确认根因：Pod 挂载卷失败，原因是 Secret 缺失。**
Pod `aiops-case-v04/workload` 中定义的卷 `input` 绑定了一个不存在的 Secret `unavailable-input`。由于该引用未被配置为可选（Optional=false），Kubelet 在初始化卷时抛出 `FailedMount` 错误。这直接导致 Pod 永远无法完成挂载步骤，从而处于 `Pending` 状态且无法创建容器。

**关键证据：**
*   **直接证据**：K8s Event `fact-b391759b75da` 记录 `secret "unavailable-input" not found`。
*   **状态证据**：K8s State `fact-05c69cddcb72` 显示 Pod 卡在 `Pending` 状态，`fact-b6c97b35ce85` 显示容器处于 `ContainerCreating` 等待中。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.9s
├─ 并发证据采集: 36.9s
│  └─ g1 aiops-case-v04/workload: 36.9s (Evidence 30.0s, RCA 6.8s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-imagepull-failed, pod-volume-mount-failed
