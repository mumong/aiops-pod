## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod workload-5dbb5dcd6c-bntfh stuck in ContainerCreating state on node2 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedCreatePodSandBox ... kubelet (combined from similar events): Failed to create pod sandbox: rpc error: code = Unknown desc = failed to setup network for sandbox ... plugin type="multus" name="multus-cni-network" failed (add): Multus: ... error loading k8s delegates k8s args: TryLoadPodDelegates: error in getting k8s network for pod: GetNetworkDelegates: failed getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` (fact-5519e3cda05, 持续约 83m) | 核心失败原因：Kubelet 明确报告 Multus 插件在尝试获取网络委派时，发现命名空间 `aiops-case-05` 下的 `unavailable-network` 定义不存在，导致沙箱创建彻底失败。 |
| 2 | K8s Event | kubernetes | 45 条 `Warning NoNetworkFound` 事件，由 `multus` 触发，内容均为 `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` (例如 fact-01aa833cf636 在 34m 前发生) | 佐证 Multus 控制器在 Pod 生命周期内反复尝试配置网络但均因缺少资源而失败，确认为持续性配置错误而非瞬时故障。 |
| 3 | K8s State | kubernetes | `container.waiting_reason`: `ContainerCreating` (fact-910269f8d2e1) | 定义 Pod 的当前停滞状态，与 K8s Event 中的失败原因互为表里，确认 Pod 未完成初始化。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: `1` (fact-9646a45492d3) | 指标确认当前 Pod 处于 Waiting 状态且原因为 `ContainerCreating`；由于仅有一个样本（`sample_count: 1`），无法评估该状态的趋势，仅作为当前状态快照。 |

**证据互证说明：**
1. **K8s Event** 提供了最完整的链路日志，明确指出 `FailedCreatePodSandBox` 是 `NoNetworkFound` 导致的，直接锁定了缺失的 `NetworkAttachmentDefinition`。
2. **K8s State** 和 **Metric** 从状态维度验证了 Pod 确实因网络插件失败而停留在 `ContainerCreating` 阶段，未进入 `Running` 或 `Waiting` 的其他原因（如 `ImagePull`、`OOMKilled`）。
3. Logging 与 Tracing 因容器未启动且无 Pod IP，属于物理上不适用，不构成证据冲突。

## 🎯 根因分析 · g1

### 因果链

```text
Deployment 声明了不存在的 Multus 网络 'unavailable-network' → Multus CNI 插件在命名空间 aiops-case-05 中找不到对应的 NetworkAttachmentDefinition 资源 → 网络沙箱（Pod Sandbox）创建失败（FailedCreatePodSandBox） → Pod 卡死在 ContainerCreating 状态
```

### 根因结论

已确认根因为：**命名空间 `aiops-case-05` 中缺失 Multus 所需的 `NetworkAttachmentDefinition` 资源 `unavailable-network`**。

*   **证据支撑**：Kubernetes Event 中的 `NoNetworkFound` 和 `FailedCreatePodSandBox` 明确指出了缺失的资源对象（`network-attachment-definitions.k8s.cncf.io "unavailable-network"` not found）。
*   **现象解释**：由于网络初始化阶段失败，Kubelet 无法创建 Pod 沙箱，导致容器无法启动，Pod 持续维持在 `ContainerCreating` 状态（见 K8s State 和 Metric）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 32.5s
├─ 并发证据采集: 40.3s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 40.3s (Evidence 33.1s, RCA 7.1s)
└─ 汇总总结: 13.7s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-imagepull-failed, pod-sandbox-create-failed
