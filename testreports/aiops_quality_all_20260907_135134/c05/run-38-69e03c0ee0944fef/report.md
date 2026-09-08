## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx in namespace aiops-case-05 is stuck in Pending/ContainerCreating state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason` = `ContainerCreating` (container: app) | 确认 Pod 处于调度后的准备阶段卡滞状态。 |
| 2 | K8s Event | multus | `NoNetworkFound`: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05) [多次发生，跨越 40m+ 周期] | 持续报错指出 Pod 尝试引用的 CNI 依赖缺失。 |
| 3 | K8s Event | kubelet | `FailedCreatePodSandBox`: failed to setup network for sandbox ... plugin type="multus" ... error loading k8s delegates: cannot find a network-attachment-definition (unavailable-network) | 记录容器运行时实际创建失败的具体机制与错误链。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` = 1 (single sample) | 通过指标验证 Pod 持续处于等待原因状态。 |

**证据说明：**
Kubernetes 事件（#2, #3）提供了详细的失败机制：kubelet 在尝试创建沙箱时，multus 插件因无法在 `aiops-case-05` 命名空间中找到名为 `unavailable-network` 的 NetworkAttachmentDefinition 而抛出错误。该错误不仅由 multus 持续上报，最终也导致 kubelet 无法完成网络配置，表现为 Pod 处于 `ContainerCreating` 状态（#1, #4）。指标与事件在状态与异常模式上相互印证。

## 🎯 根因分析 · g1

### 因果链

```text
NetworkAttachmentDefinition 'unavailable-network' 在命名空间 aiops-case-05 中不存在 → Multus CNI 插件无法加载网络委托 → Pod 沙箱创建失败 (kubelet error) → Pod 卡在 ContainerCreating/Pending 状态
```

### 根因结论

已确认的根因是：Pod `workload-5dbb5dcd6c-kbwsx` 配置的 Multus CNI 引用了一个在 `aiops-case-05` 命名空间中不存在的 NetworkAttachmentDefinition 资源（`unavailable-network`）。

该配置缺失导致 Multus 插件在尝试为 Pod 建立网络环境时直接失败，从而引发 kubelet 无法创建 Pod 沙箱（`FailedCreatePodSandBox`），最终表现为容器处于 `ContainerCreating` 的等待状态。事实关联完整且错误信息明确，无需补充其他维度的决定性证据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 24.3s
├─ 并发证据采集: 68.9s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 68.9s (Evidence 59.5s, RCA 9.2s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed, pod-sandbox-create-failed
