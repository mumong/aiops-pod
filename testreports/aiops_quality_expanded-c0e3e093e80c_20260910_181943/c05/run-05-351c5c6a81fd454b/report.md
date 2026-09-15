## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-bntfh 配置引用了不存在的 Multus NetworkAttachmentDefinition 'unavailable-network'，导致 Multus CNI 插件抛出 NoNetworkFound 错误，Kubelet 无法创建 Pod Sandbox，从而使 Pod 持续处于 Pending/ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `FailedCreatePodSandBox`：failed to setup network for sandbox: plugin type="multus" name="multus-cni-network" failed (add): Multus: ... GetNetworkDelegates: failed getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05) | 明确指出了 Pod 创建失败的根本原因是 CNI 网络插件无法找到指定的网络资源定义。 |
| 2 | K8s Event | multus | `NoNetworkFound`：cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found | 由 Multus 插件直接触发的特定错误事件，确认了 `unavailable-network` 这一特定资源在目标命名空间中的缺失。 |
| 3 | K8s State | Kubernetes | `container.waiting_reason`: `ContainerCreating` | 确认容器卡在等待阶段，且该状态已被 Kubelet 的失败事件持续印证，排除了资源调度问题。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (container: app, reason: ContainerCreating): value `1` (single sample) | 从监控层面确认了 `ContainerCreating` 状态的真实存在，与事件记录一致。 |

**证据链印证说明：**
Kubelet 报告 `FailedCreatePodSandBox` 是因为网络设置失败，而底层 Multus 插件明确抛出了 `NoNetworkFound`，原因正是引用了不存在的 `network-attachment-definitions` 资源 `unavailable-network`。Metrics 和 State 状态（`ContainerCreating`）均佐证了这一故障导致容器无法进入运行状态，且无其他干扰因素。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了不存在的 Multus NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件执行失败 (NoNetworkFound) → Kubelet 无法创建 Pod Sandbox (FailedCreatePodSandBox) → Pod 持续处于 ContainerCreating 状态 [1,2,3]
```

### 根因结论

**已确认根因**：Pod `aiops-case-05/workload-5dbb5dcd6c-bntfh` 的网络配置引用了一个在该 Namespace (`aiops-case-05`) 中不存在的 Multus 网络定义资源 `unavailable-network`（证据 [1]、[2]）。这导致 Multus 插件在尝试配置网络时抛出 `NoNetworkFound` 错误，进而致使 Kubelet 创建 Sandbox 失败，Pod 无法启动（证据 [3]）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 21.3s
├─ 并发证据采集: 53.1s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 53.1s (Evidence 44.7s, RCA 8.2s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed, pod-imagepull-failed
