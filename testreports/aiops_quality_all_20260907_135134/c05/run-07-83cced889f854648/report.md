## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod 配置了引用不存在网络附件定义（'unavailable-network'）的 Multus CNI 注解，导致 Multus 插件无法完成网络初始化，进而阻塞 Kubelet 创建 Pod Sandbox，最终使 Pod 卡死在 ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: `ContainerCreating` (container: app) | 确认 Pod 处于初始化阻塞状态 |
| 2 | K8s Event | kubelet | `FailedCreatePodSandBox`: rpc error: failed to setup network for sandbox... `failed getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 确立网络插件查找失败的直接报错与上下文 |
| 3 | K8s Event | multus | `NoNetworkFound`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` | 确认底层 Multus 组件的具体错误为缺失命名资源 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` [container: "app", reason: "ContainerCreating"]: `1` | 指标确认容器等待原因为启动中 |

**证据关联分析：**
- **事实 1** 展示 Pod 处于 `ContainerCreating` 状态，表明容器未成功拉起。
- **事实 2 和 3** 分别从 Kubelet 和 Multus 两个视角确认了导致该状态的直接原因：Multus 在 `aiops-case-05` 命名空间中查找网络附件定义 `unavailable-network` 失败，导致网络初始化无法完成。
- **事实 4** 作为补充指标数据，与 K8s Event 的报错原因相互印证，共同指向因网络资源缺失导致的初始化阻塞。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 配置引用不存在的网络定义 unavailable-network → Multus CNI 插件查找网络资源失败 → Kubelet 无法初始化 Pod Sandbox 网络 → Pod 状态停留在 ContainerCreating
```

### 根因结论

已确认根因为 **Pod 配置了引用不存在网络附件定义的 Multus CNI 注解**。

证据链显示，Kubelet 在尝试创建 Pod Sandbox 时，Multus 插件尝试加载 k8s delegates 并获取网络定义，但由于命名空间 `aiops-case-05` 中不存在名为 `unavailable-network` 的 `network-attachment-definitions` 资源，导致网络插件报错失败 (`failed getting the delegate`)。这一失败使得 Kubelet 无法完成网络初始化，进而将 Pod 卡在 `ContainerCreating` 状态 (证据编号 1, 2, 3, 4)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 23.1s
├─ 并发证据采集: 70.7s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 70.7s (Evidence 61.2s, RCA 9.3s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-sandbox-create-failed
