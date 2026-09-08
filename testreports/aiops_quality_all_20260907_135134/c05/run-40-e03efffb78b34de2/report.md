## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-kbwsx stuck in ContainerCreating state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: `ContainerCreating` | 证实 Pod 当前处于创建阻塞状态，未进入运行态 |
| 2 | K8s Event | multus | `NoNetworkFound` (46条记录, 持续 60m): `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 提供决定性证据，指出 Multus CNI 插件在尝试获取网络配置时，因目标 `NetworkAttachmentDefinition` 资源不存在而持续报错 |
| 3 | K8s Event | kubelet | `FailedCreatePodSandBox` (379次): `failed to setup network for sandbox ... plugin type="multus" ... error in getting k8s network for pod: ... cannot find a network-attachment-definition (unavailable-network)` | 证实底层 kubelet 创建 Pod 沙箱因网络插件失败而回退，与上层事件因果闭环 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating", container="app"}` 当前值为 `1` | 确认容器持续等待中，由于样本数不足 (`sample_count: 1`)，未观察到趋势变化，与事件时间范围一致 |

**证据互证说明：**
1. **K8s State** 确认了故障现象（`ContainerCreating`）。
2. **K8s Event** 中的 `multus` 和 `kubelet` 事件在时间上重叠，内容上高度一致，共同指向唯一的失败原因：缺少名为 `unavailable-network` 的 `NetworkAttachmentDefinition` 资源。
3. **Metric** 进一步佐证了该状态在监控时刻依然持续存在。

## 🎯 根因分析 · g1

### 因果链
```text
缺少 NetworkAttachmentDefinition 资源 'unavailable-network' (事实 #1)
    → Multus CNI 插件无法获取网络配置 (事实 #2)
    → Pod Sandbox 网络初始化失败 (事实 #3)
    → Pod 持续处于 ContainerCreating 状态 (事实 #4)
```

### 根因结论
已确认的根因为 **缺失 NetworkAttachmentDefinition 资源**。
Pod `workload-5dbb5dcd6c-kbwsx` 的 PodSpec 中引用了名为 `unavailable-network` 的网络定义，但在 `aiops-case-05` 命名空间中该资源不存在。这导致 Multus CNI 插件在容器创建阶段无法完成网络挂载，进而使 kubelet 创建 Pod 沙箱失败，Pod 因此一直卡在 `ContainerCreating` 状态。事实 #2 和 #3 提供了直接且一致的因果关系支持。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 19.2s
├─ 并发证据采集: 49.8s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 49.8s (Evidence 41.7s, RCA 7.9s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-sandbox-create-failed
