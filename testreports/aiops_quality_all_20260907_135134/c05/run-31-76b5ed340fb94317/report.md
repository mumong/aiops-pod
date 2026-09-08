## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-kbwsx 配置了 Multus CNI 注解 `k8s.v1.cni.cncf.io/networks: unavailable-network`，但在该命名空间下不存在对应的 `NetworkAttachmentDefinition` 资源。这导致 Multus 插件在初始化 Pod Sandbox 时找不到网络定义并报错，引发 kubelet 持续抛出 `FailedCreatePodSandBox` 事件，使 Pod 卡在 `Pending` 和 `ContainerCreating` 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Container `app` waiting_reason: `ContainerCreating` (fact_id: fact-abc14a739178) | 确认 Pod 处于初始化停滞状态，容器尚未启动。 |
| 2 | K8s Event | Kubernetes | `Warning NoNetworkFound ... multus cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` (fact_id: fact-06dc0978b4c2) | 直接指明 Multus CNI 插件在尝试查找指定网络定义时失败。 |
| 3 | K8s Event | Kubernetes | `Warning FailedCreatePodSandBox ... rpc error: code = Unknown desc = failed to setup network for sandbox ... plugin type="multus" ... error in getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) ... not found` (fact_id: fact-65eeefa14f6b) | 确认底层失败机制为 Pod Sandbox 创建时 Multus 网络插件初始化网络失败。 |

**证据印证说明：**
状态面显示容器卡在 `ContainerCreating`；事件面提供了明确的失败原因链：Pod 配置的 `unavailable-network` 网络注解在命名空间 `aiops-case-05` 中不存在，导致 Multus 插件无法加载网络配置，进而引发 `FailedCreatePodSandBox` 错误，解释了容器无法启动的直接原因。

## 🎯 根因分析 · g1

### 因果链

```text
缺少 NetworkAttachmentDefinition "unavailable-network" → Multus 插件初始化网络失败 → Pod Sandbox 创建失败 (FailedCreatePodSandBox) → Pod 卡在 ContainerCreating 状态
```

### 根因结论

已确认根因为 **网络配置缺失**。Pod `aiops-case-05/workload-5dbb5dcd6c-kbwsx` 配置了引用 `unavailable-network` 的 Multus CNI 注解，但 `aiops-case-05` 命名空间下不存在对应的 `NetworkAttachmentDefinition` 资源（事实 #2 和 #3）。这导致 Multus 插件在初始化网络时找不到定义并报错，最终使得 kubelet 无法创建 Pod Sandbox（事实 #3），导致容器状态持续为 `ContainerCreating`（事实 #1）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.0s
├─ 并发证据采集: 49.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 49.5s (Evidence 41.6s, RCA 7.8s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed
