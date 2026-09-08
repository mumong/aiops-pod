## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-nhd7v 依赖的 NetworkAttachmentDefinition 'unavailable-network' 缺失，导致 Multus CNI 无法配置网络并创建 Pod 沙箱。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `multus` | `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` | 直接指出 Multus CNI 在尝试为 Pod 配置网络时，因找不到指定名称的 NetworkAttachmentDefinition 而失败。 |
| 2 | K8s Event | `kubelet` | `Failed to create pod sandbox: ... plugin type="multus" name="multus-cni-network" failed (add): ... getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 确认 kubelet 创建 Pod 沙箱失败，根本原因为 Multus 插件调用失败，且失败原因一致指向上述 NetworkAttachmentDefinition 缺失。 |
| 3 | K8s State | `Kubernetes` | `container.waiting_reason: {"container": "app", "reason": "ContainerCreating"}` | 证实容器处于等待状态，状态与 CNI 网络配置失败导致无法创建沙箱的现象一致。 |
| 4 | Metric | `Prometheus` | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1` | 独立验证了容器处于 `ContainerCreating` 等待原因，与 K8s State 证据一致。 |

**证据链分析：**
K8s Event（#1, #2）提供了具体的失败堆栈和错误信息，明确指出失败是 `unavailable-network` 资源缺失所致；K8s State（#3）和 Metric（#4）从不同维度证实了该 Pod 处于网络准备阶段的阻塞状态。这些证据互相印证，构成了完整的故障现象到原因的闭环。

## 🎯 根因分析 · g1

### 因果链

```text
缺失 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件无法获取网络代理配置 → Pod 沙箱创建失败 (rpc error) → Pod 卡在 ContainerCreating 状态
```

### 根因结论

已确认的根因是 Pod `aiops-case-05/workload-5dbb5dcd6c-nhd7v` 在配置网络时，引用了一个不存在的 `NetworkAttachmentDefinition` 资源 `unavailable-network`。

这直接导致 Multus CNI 插件在尝试配置网络时失败，进而使得 kubelet 无法创建 Pod 沙箱，最终表现为 Pod 卡在 `ContainerCreating` 状态（证据 #1, #2, #3, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 32.8s
├─ 并发证据采集: 52.8s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 52.8s (Evidence 46.5s, RCA 6.2s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed, pod-terminating-stuck
