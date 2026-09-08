## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-nhd7v 引用了不存在的 NetworkAttachmentDefinition 'unavailable-network'，导致 Multus CNI 插件无法配置网络，Pod 无限期卡在 ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Failed to create pod sandbox: ... plugin type="multus" name="multus-cni-network" failed (add): Multus: ... error loading k8s delegates k8s args: TryLoadPodDelegates: error in getting k8s network for pod: GetNetworkDelegates: failed getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` (fact-10849248dfe8) | 明确展示了 kubelet 调用 Multus 插件失败的详细调用链与缺失资源对象，指向根因 |
| 2 | K8s Event | kubernetes | `Warning NoNetworkFound multus cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (fact-01e4ee82b165, fact-081eb57ffc71 等) | 在 pod 启动的长时间窗口内持续触发同一错误事件，证明故障持续存在且未自愈 |
| 3 | K8s State | kubernetes | `ContainerCreating` 状态，reason: `ContainerCreating` (fact-2a27f02d4951) | 确认 Pod 当前处于等待配置网络的阻塞状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 `1`，labels: `reason=ContainerCreating` (fact-00d78e74e767) | 确认集群中该 Pod 处于 Waiting 状态的客观计量数据，与状态一致 |

**证据说明：**
Kubernetes 的 State 与 Metric 数据一致确认 Pod 处于等待状态。所有诊断价值集中于 K8s Event，kubelet 层面的 `FailedCreatePodSandBox` 错误（#1）包含了深层的 Multus 代理调用失败详情，而高频的 `NoNetworkFound` 警告（#2）证实了该依赖资源的长期缺失，两者结合直接锁定了故障源头。

## 🎯 根因分析 · g1

### 因果链

```text
引用不存在的 NetworkAttachmentDefinition 'unavailable-network' → Multus 插件尝试加载网络代理配置失败 → Pod 沙箱创建失败 (Sandbox creation failed) → Pod 卡在 ContainerCreating 状态
```

### 根因结论

**已确认根因**：Pod `aiops-case-05/workload-5dbb5dcd6c-nhd7v` 配置了引用 `unavailable-network` 的 Multus 网络依赖，但目标 `NetworkAttachmentDefinition` 对象在 `aiops-case-05` 命名空间中不存在。这一配置缺陷导致 Multus CNI 插件在执行网络配置时抛出 `not found` 错误，致使 Pod 无法完成网络沙箱建立，从而无限期阻塞在 `ContainerCreating` 状态。该结论由详细的 Event 日志调用链（事实 #1、#2）和容器状态数据（事实 #3）相互印证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 48.2s
├─ 并发证据采集: 44.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 44.5s (Evidence 38.1s, RCA 6.3s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-sandbox-create-failed, pod-volume-mount-failed
