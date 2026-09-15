## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod workload-5dbb5dcd6c-bntfh in namespace aiops-case-05 is stuck in ContainerCreating/Pending state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | multus (Namespace: aiops-case-05) | 46次 `NoNetworkFound` 警告，明确指出 `network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found`（时间跨度：2s - 60m） | 确凿证据：证明 Multus 持续无法解析 Pod 引用的网络资源 |
| 2 | K8s Event | kubelet (Namespace: aiops-case-05) | `FailedCreatePodSandBox`，错误详情：`plugin type="multus" ... failed to setup network for sandbox ... cannot find a network-attachment-definition ... "unavailable-network" not found` | 确凿证据：展示 Kubelet 因底层 CNI 失败而拒绝创建沙箱 |
| 3 | K8s State | Kubelet | 容器 `app` 状态维持在 `ContainerCreating`，等待理由为 `ContainerCreating` | 现象证据：证实 Pod 处于卡滞状态，未能推进到 Running |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 辅助证据：外部指标验证了 Pod 确实处于等待状态 |

**证据说明**：
Multus CNI 和 Kubelet 发出的两个不同维度的 K8s Event（#1, #2）均指向完全相同的缺失资源 `unavailable-network`，这种跨组件的事实一致性强有力地锁定了配置错误。Metric 和 K8s State 分别独立观测到了 Pod 无法启动的现象（#3, #4），与事件日志描述的状态完全吻合。

## 🎯 根因分析 · g1

### 因果链

```text
缺失网络资源 'unavailable-network' (Namespace: aiops-case-05) → Multus CNI 失败解析网络委托 → Kubelet 无法创建 Pod 沙箱 (FailedCreatePodSandBox) → Pod 卡滞在 ContainerCreating 状态
```

### 根因结论

**已确认根因：缺失网络定义资源导致 Multus 网络初始化失败。**

Pod `workload-5dbb5dcd6c-bntfh` 在创建过程中配置了 Multus 网络引用，但其命名空间 `aiops-case-05` 中不存在名为 `unavailable-network` 的 `NetworkAttachmentDefinition` 资源（见证据 #1 和 #2）。这一配置错误导致 Multus CNI 插件无法初始化网络，进而触发 Kubelet 拒绝创建 Pod 沙箱，最终导致 Pod 无限期停留在 `ContainerCreating` 状态（见证据 #3 和 #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.9s
├─ 并发证据采集: 45.1s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 45.1s (Evidence 36.8s, RCA 8.1s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed, pod-config-error, pod-imagepull-failed
