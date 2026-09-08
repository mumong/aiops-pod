## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx stuck in ContainerCreating (Pending) due to sandbox creation failure. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: container="app", reason="ContainerCreating" | 确认 Pod 处于启动卡滞状态，未进入 Running 阶段。 |
| 2 | K8s Event | kubernetes | `FailedCreatePodSandBox` (57m, 56m): "failed to setup network for sandbox... plugin type=\"multus\"... GetNetworkDelegates: failed getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io \"unavailable-network\" not found" | 直接指示 kubelet 在尝试创建 Pod 网络命名空间时失败，根本原因为找不到指定的 CNI 定义。 |
| 3 | K8s Event | kubernetes | `NoNetworkFound` (55m-2s): "cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io \"unavailable-network\" not found" | 多源（Multus）持续报错，证实该缺失定义是一个持续性的、非偶发的配置错误，而非临时网络不可用。 |

**证据综述：**
Metric 数据与 K8s 事件相互印证（证据 1 与 2）。Pod 持续处于等待状态，并非资源不足，而是被特定的网络插件失败逻辑阻断。由于 Pod 无法启动，Logging 和 Tracing 维度被判定为不适用（No logs/Traces generated），因此故障定位完全依赖 K8s 的控制平面事件。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Annotation 引用不存在的 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件尝试加载 Delegate 时查找失败 (getKubernetesDelegate failed) → Kubelet 创建沙箱失败 (FailedCreatePodSandBox) → Pod 卡在 ContainerCreating (Pending)
```

### 根因结论

已确认根因为：**Pod 引用的 CNI 网络定义缺失**。

Pod `workload-5dbb5dcd6c-kbwsx` 的配置（通过 Annotation 隐式引用或配置）指向名为 `unavailable-network` 的 `NetworkAttachmentDefinition`。证据显示，在 `aiops-case-05` 命名空间中，该 CRD 资源不存在。这导致 Multus 插件无法获取网络配置并设置 Pod 沙箱网络，进而引发 `FailedCreatePodSandBox` 错误，使 Pod 永久停留在 `ContainerCreating` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 22.9s
├─ 并发证据采集: 44.3s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 44.3s (Evidence 36.4s, RCA 7.7s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-imagepull-failed, pod-sandbox-create-failed
