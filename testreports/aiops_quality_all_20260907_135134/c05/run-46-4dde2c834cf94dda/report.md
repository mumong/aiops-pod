## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-kbwsx 的 annotation `k8s.v1.cni.cncf.io/networks` 配置了名为 `unavailable-network` 的 CNI 网络附件，但在 namespace `aiops-case-05` 中不存在对应的 NetworkAttachmentDefinition CRD 资源，导致 Multus CNI 插件无法创建 Pod sandbox。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (multus) | Warning NoNetworkFound: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found (fact-01d62034766f) | 指出 Multus 插件在查找特定网络配置时失败的具体报错信息，频率极高。 |
| 2 | K8s Event | kubernetes (kubelet) | Warning FailedCreatePodSandBox: failed setup network for sandbox... error getting the delegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05) not found (fact-caedf51253a1) | 确认上述网络查找失败直接导致 Pod 的容器沙箱创建过程被中止。 |
| 3 | K8s State | kubernetes | `container.waiting_reason`: ContainerCreating (fact-800079748146) | 描述 Pod 当前处于等待网络资源就绪的阻塞状态。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: 1 (fact-1c37aa09ec47) | 量化证实该 Pod 当前正持续处于等待状态，符合 K8s State 描述。 |

**证据小结：**
Kubernetes 事件提供了最直接的诊断依据：事件 `NoNetworkFound` 和 `FailedCreatePodSandBox` 高度一致地指出了缺失的网络定义资源（`unavailable-network`）是阻塞点。Metric 和 K8s State 均从侧面印证了这一阻塞导致容器无法启动（`ContainerCreating`），所有数据源指向同一原因。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用不存在的 NAD CRD (unavailable-network) → Multus 插件查找网络定义失败 → 容器沙箱创建中断 → Pod 卡在 ContainerCreating 状态
```

### 根因结论

**已确认根因：**
Pod `aiops-case-05/workload-5dbb5dcd6c-kbwsx` 的 `k8s.v1.cni.cncf.io/networks` 注解中引用了名为 `unavailable-network` 的 CNI 网络附件，但在 `aiops-case-05` 命名空间下缺失对应的 `NetworkAttachmentDefinition` CRD 资源。这一配置错误导致 Multus CNI 插件无法解析网络配置，进而引发容器沙箱创建失败（证据编号 1, 2），最终使 Pod 卡在 `ContainerCreating` 状态（证据编号 3, 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 20.4s
├─ 并发证据采集: 55.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 55.5s (Evidence 48.1s, RCA 7.2s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed, pod-imagepull-failed
