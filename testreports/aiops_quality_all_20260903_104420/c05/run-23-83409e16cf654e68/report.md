## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod 配置引用了不存在的 NetworkAttachmentDefinition 'unavailable-network'，导致 Multus CNI 无法创建 Pod 沙箱，致使容器无限期停留在 ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning NoNetworkFound ... multus: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` (fact-01c709de96b0) | 直接指明 K8s 网络插件 Multus 无法找到名为 `unavailable-network` 的网络资源定义 |
| 2 | K8s Event | kubernetes | `Warning FailedCreatePodSandBox ... kubelet: Failed to create pod sandbox: ... plugin type="multus" ... GetNetworkDelegates: cannot find a network-attachment-definition (unavailable-network) ... "unavailable-network" not found` (fact-148e77eaa6c2) | 确认沙箱创建失败的根本原因是 Multus 获取网络代理（delegate）时网络定义缺失 |
| 3 | K8s State | kubernetes | `container.waiting_reason: ContainerCreating` (fact-902cc704dd41) | 描述 Pod 因网络依赖未满足而无限期阻塞在容器创建等待状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1` (fact-438edc096748) | 度量指标确认了 Pod 处于 `ContainerCreating` 等待状态的客观事实 |

Kubernetes 事件表明 Multus CNI 在尝试初始化 Pod 网络时，因为找不到 `unavailable-network` 资源而报错，直接导致 kubelet 创建沙箱失败。这一网络层面的配置缺失是 Pod 状态长期停留在 `ContainerCreating` 且未向前推进的直接原因。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了不存在的 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 获取网络代理失败 (GetNetworkDelegates) → 无法创建 Pod 沙箱 → Pod 无限期停留在 ContainerCreating 状态
```

### 根因结论

已确认根因：**Pod 配置引用了不存在的网络定义资源。**

Pod 配置中指定了 `NetworkAttachmentDefinition` 名为 `unavailable-network`，但该资源在 `aiops-case-05` 命名空间中不存在。由于 Multus CNI 强依赖此资源来配置网络插件，该缺失导致 Pod 沙箱无法初始化，从而使得容器无法启动，一直处于 `ContainerCreating` 等待状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 37.3s
├─ 并发证据采集: 49.6s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 49.6s (Evidence 43.0s, RCA 6.4s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-sandbox-create-failed, pod-imagepull-failed
