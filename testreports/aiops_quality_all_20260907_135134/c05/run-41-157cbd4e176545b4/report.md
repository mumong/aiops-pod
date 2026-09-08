## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx in namespace aiops-case-05 stuck in ContainerCreating/Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: ContainerCreating (fact-id: fact-c462f10abbdc) | 确认 Pod `workload-5dbb5dcd6c-kbwsx` 处于启动挂起状态。 |
| 2 | K8s Event | kubernetes | `NoNetworkFound`: "cannot find a network-attachment-definition (unavailable-network)... 'unavailable-network' not found" (fact-id: fact-080c47f7e77b) | 直接归因于 Multus 无法在 `aiops-case-05` 命名空间找到定义的 CNI 网络插件。 |
| 3 | K8s Event | kubernetes | `FailedCreatePodSandBox`: "failed setup network... plugin type=multus... getKubernetesDelegate: cannot find a network-attachment-definition..." (fact-id: fact-a32ca05aaecf) | 提供底层沙箱创建失败的堆栈信息，印证网络缺失导致 Kubelet 调度失败。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason=ContainerCreating) (fact-id: fact-f8075f92e5bb) | 指标证实 Pod 持续处于等待状态，未恢复正常。 |

**证据综合：**
Kubernetes 事件日志（证据 #2, #3）提供了确凿的错误根源：Pod 依赖的 `unavailable-network` 网络附件定义不存在，导致 Multus CNI 在构建 Pod 沙箱时彻底失败。Metric 数据（证据 #4）从指标层面确认了该状态是持续的，而容器状态（证据 #1）直观反映了此结果。日志与 Tracing 维度因 Pod 未启动无法采集，故由多维 K8s 事实独立支撑结论。

## 🎯 根因分析 · g1

### 因果链

```text
NetworkAttachmentDefinition 'unavailable-network' 缺失 → Multus CNI 解析失败 → Kubelet 创建 Pod 沙箱失败 (NoNetworkFound) → Pod 卡死在 ContainerCreating/Pending 状态
```

### 根因结论

已确认根因为 **命名空间 `aiops-case-05` 中缺少 Pod 声明依赖的 `NetworkAttachmentDefinition` 资源 `unavailable-network`**。

该缺失导致 Multus 在调用 CNI 插件时无法获取网络配置，从而持续抛出 `NoNetworkFound` 警告事件，并触发 Kubelet 的 `FailedCreatePodSandBox` 错误，最终使容器无法启动（证据 #2, #3, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.2s
├─ 并发证据采集: 51.1s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 51.1s (Evidence 41.1s, RCA 9.8s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed
