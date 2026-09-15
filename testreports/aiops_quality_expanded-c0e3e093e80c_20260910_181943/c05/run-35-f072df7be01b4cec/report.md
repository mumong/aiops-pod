## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod YAML 中引用了名为 'unavailable-network' 的 NetworkAttachmentDefinition，但该资源在 aiops-case-05 命名空间中不存在，导致 Multus CNI 插件无法创建 Pod 网络沙箱。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `ContainerCreating` (container: app, fact-2e422a724482) | 确认容器处于未就绪的等待状态。 |
| 2 | K8s Event | multus | `NoNetworkFound` (fact-01a1dd37f990, 重复 46 次): `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 明确报错 Multus 插件在 `aiops-case-05` 命名空间下找不到名为 `unavailable-network` 的资源。 |
| 3 | K8s Event | kubelet | `FailedCreatePodSandBox` (fact-12589ce378d7, 重复 356 次): `rpc error: code = Unknown desc = ... network for sandbox ... plugin type="multus" ... failed ... network-attachment-definitions ... not found` | 确认 kubelet 因 Multus 网络插件失败而无法创建 Pod 沙箱，是直接的失败机制。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1 (container: app, reason: ContainerCreating, fact-1598b2446076) | 通过指标确认应用容器 `app` 确实卡在 `ContainerCreating` 状态。 |

**证据关联说明：**
Kubernetes 状态 (`ContainerCreating`) 和 Metric 数据一致，确认了异常现象。根本原因由两个维度的 Event 闭环证实：`multus` 插件反复报错找不到 `unavailable-network` 网络定义，直接导致了 `kubelet` 执行 `FailedCreatePodSandBox`，使得 Pod 无法进入运行状态。由于容器无法启动，日志与追踪数据被正确判定为不适用（`not_applicable`）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用不存在的 NetworkAttachmentDefinition 'unavailable-network' 
→ Multus CNI 插件在配置网络时无法找到定义 (NoNetworkFound) 
→ kubelet 执行 FailedCreatePodSandBox 并报错 'network-attachment-definitions ... not found' 
→ Pod 状态停留在 ContainerCreating
```

### 根因结论

已确认的根因为：Pod YAML 中配置引用的 `NetworkAttachmentDefinition` 资源名为 `'unavailable-network'`，但该资源在 `aiops-case-05` 命名空间中不存在。

该缺失资源导致 Multus CNI 插件在初始化网络时无法获取网络配置，触发 `NoNetworkFound` 错误，进而致使 kubelet 创建 Pod 网络沙箱（Sandbox）失败，最终表现为 Pod 持续处于 `ContainerCreating` 状态。证据链包含重复出现的 `multus` 错误日志与 `kubelet` 失败事件，因果关系明确，证据充分。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.3s
├─ 并发证据采集: 42.2s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 42.2s (Evidence 35.5s, RCA 6.6s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed
