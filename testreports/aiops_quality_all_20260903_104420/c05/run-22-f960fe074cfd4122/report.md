## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-nhd7v stuck in Pending/ContainerCreating state on node2 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubelet/Multus | `FailedCreatePodSandBox` (fact-092e67d3d4cd, fact-62292ab7d32d 等): `rpc error: code = Unknown desc = ... Multus: ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` | 直接证明 Pod 因网络插件无法找到指定网络定义而创建失败，形成循环阻塞。 |
| 2 | K8s Event | Multus | `NoNetworkFound` (fact-015d3f441525, fact-01cf068d8169 等, 累积 47 次): `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 提供高频复现的证据，确认 `unavailable-network` 引用无效，是故障触发的核心原因。 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (fact-295ebd86e836): Reason=`ContainerCreating` (当前值=1) | 确认 Pod 处于持续等待状态，与事件日志中的阻塞现象一致。 |
| 4 | K8s State | Pod Spec | Entity: `aiops-case-05/workload-5dbb5dcd6c-nhd7v`, Status: `ContainerCreating` (diagnostic_status: `diagnosed`) | 锚定故障实体的生命周期状态，表明 Pod 尚未进入运行阶段。 |

**证据印证：**
- 事件（#1, #2）明确指出了 `network-attachment-definitions.k8s.cncf.io "unavailable-network" not found`，这既是 Kubelet 报错 `FailedCreatePodSandBox` 的直接原因，也是 Multus 反复产生 `NoNetworkFound` 的原因。
- Metric（#3）确认了 Pod 状态为 `ContainerCreating`，符合因网络配置错误导致无法完成沙箱创建进而无法启动容器的预期行为。
- 日志与追踪未采集（状态为 `not_applicable`），因为容器物理上未启动，但 K8s 内部事件已完整覆盖故障因果链。

## 🎯 根因分析 · g1

### 因果链

```text
Namespace 'aiops-case-05' 中缺少 NetworkAttachmentDefinition 'unavailable-network' 
→ Multus CNI 在初始化 Pod 沙箱时解析网络附件失败 (NoNetworkFound) 
→ Kubelet 报告 FailedCreatePodSandBox 并拒绝创建容器 
→ Pod 停留在 ContainerCreating 状态无法重启
```

### 根因结论

已确认根因：Pod `aiops-case-05/workload-5dbb5dcd6c-nhd7v` 的容器启动被阻塞，因为 Multus CNI 插件依赖一个不存在的 `NetworkAttachmentDefinition` 资源（名称：`unavailable-network`）。

- **故障机制**：Pod 配置中引用了名为 `unavailable-network` 的网络附件定义，但该资源在 `aiops-case-05` 命名空间中未创建。
- **证据支撑**：Kubelet 事件 `fact-092e67d3d4cd` 显示 `FailedCreatePodSandBox` 根本原因为 Multus 找不到该网络定义；Multus 事件 `fact-015d3f441525` 连续 47 次报出 `NoNetworkFound` 错误；Metric `fact-295ebd86e836` 确认 Pod 持续处于 `ContainerCreating` 等待状态。
- **结论**：缺失的 `NetworkAttachmentDefinition` 资源是导致当前 Pod 无法启动的直接且唯一根因。

---

## 📊 性能统计

```text
├─ 总耗时: 10.0m
├─ 问题定位: 29.8s
├─ 并发证据采集: 557.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 557.5s (Evidence 548.3s, RCA 9.1s)
└─ 汇总总结: 13.5s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed
