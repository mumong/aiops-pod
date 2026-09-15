## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-bntfh 注解引用了不存在的 Multus 网络定义 'unavailable-network'，导致 Multus CNI 插件在创建 Pod 沙箱时找不到对应的 NetworkAttachmentDefinition 资源，引发 kubelet 持续报 FailedCreatePodSandBox 错误，使 Pod 卡在 Pending/ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `NoNetworkFound`: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found (fact-07ed08503cb0) | 直接指明 Multus CNI 在命名空间 `aiops-case-05` 中找不到名为 `unavailable-network` 的网络定义资源，构成缺失依赖。 |
| 2 | K8s Event | kubernetes | `FailedCreatePodSandBox`: failed to setup network for sandbox ... plugin type="multus" ... GetNetworkDelegates: failed getting the delegate ... network-attachment-definitions.k8s.cncf.io "unavailable-network" not found (fact-030ac984ab22) | 确认 kubelet 因无法获取网络配置导致沙箱创建失败，该错误由网络依赖缺失直接触发。 |
| 3 | K8s State | kubernetes | `ContainerCreating` (container: app) (fact-2a3aeb027022) | 反映 Pod 处于等待状态，其根本原因是容器初始化阶段因网络插件故障被阻塞。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating", container="app"} = 1` (fact-df55559cda68) | 从指标层面量化确认容器处于 `ContainerCreating` 等待状态，佐证了 K8s 事件描述的运行状态异常。 |

**证据关联说明**：
K8s Event 中的 `NoNetworkFound`（事实 1）与 `FailedCreatePodSandBox`（事实 2）存在因果链，分别由 Multus 插件和 kubelet 上报，共同证实了 `unavailable-network` 资源缺失导致网络配置失败；Metric 事实（事实 4）独立确认了容器处于 `ContainerCreating` 状态，与事件描述的现象完全一致。

## 🎯 根因分析 · g1

### 因果链

```text
缺失 Multus 网络定义 'unavailable-network' → Multus CNI 插件无法加载 k8s 委托网络配置 → kubelet 创建 Pod 沙箱（失败） → 容器卡在 ContainerCreating 状态
```

### 根因结论

已确认的根因为：**Pod `aiops-case-05/workload-5dbb5dcd6c-bntfh` 的注解引用了不存在的 Multus 网络定义 `unavailable-network`**。

**证据支撑**：
Kubernetes 事件事实（#1, #2）明确记录了 `network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` 错误，证实了 Pod 尝试获取的网络资源在当前命名空间中不存在。该缺失导致 Multus 插件无法完成网络配置，进而引发 `FailedCreatePodSandBox` 错误，最终导致容器无法启动而卡在 `ContainerCreating` 状态（#3, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 19.3s
├─ 并发证据采集: 54.1s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 54.1s (Evidence 46.5s, RCA 7.5s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed
