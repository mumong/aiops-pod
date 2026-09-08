## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx 处于 Pending 状态，容器 app 卡在 ContainerCreating，未能创建网络 sandbox。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedCreatePodSandBox 69s (x402 over 89m) kubelet: Failed to create pod sandbox: rpc error... plugin type="multus"... error in getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 直接表明 kubelet 无法为 Pod 创建网络环境，错误根源指向 Multus 插件无法获取指定的网络定义 |
| 2 | K8s Event | kubernetes | `Warning NoNetworkFound 9s multus: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` | 持续报错证明 Multus 插件持续尝试查找名为 `unavailable-network` 的网络定义但均未找到 |
| 3 | K8s State | kubernetes | `container.waiting_reason: ContainerCreating` | 容器状态停滞在创建阶段，因网络资源缺失导致无法进入运行状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 当前值 `1`，Labels: `reason=ContainerCreating` | 验证了当前 Pod 处于等待状态且原因为网络/沙箱创建失败，符合事件反映的现象 |

**证据总结：**
事件流中连续不断的 `NoNetworkFound` 警告与 kubelet 的 `FailedCreatePodSandBox` 错误相互印证，明确指出失败原因是指定的 Multus 网络定义 `unavailable-network` 在命名空间 `aiops-case-05` 中不存在，这直接阻碍了网络沙箱的建立，导致 Pod 永久卡在 `ContainerCreating`。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 注解引用不存在的网络定义 'unavailable-network' → Multus CNI 插件找不到对应资源 → 网络沙箱创建失败 (NoNetworkFound) → Pod 卡在 ContainerCreating
```

### 根因结论

**已确认的根因：** Pod `workload-5dbb5dcd6c-kbwsx` 引用了 Multus CNI 插件中一个在命名空间 `aiops-case-05` 中并不存在的网络附加定义（NetworkAttachmentDefinition）`unavailable-network`。

**因果解释：**
当 Pod 启动时，Multus 插件尝试根据 Pod 注解加载该网络定义以初始化容器网络，但由于该定义在集群中缺失（见证据 #1 和 #2），导致网络沙箱（Pod Sandbox）创建失败。这直接使得容器无法获取网络接口，从而被 Kubernetes 保持在 `ContainerCreating` 状态，无法进入 `Running` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 19.9s
├─ 并发证据采集: 46.4s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 46.4s (Evidence 36.9s, RCA 9.3s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed
