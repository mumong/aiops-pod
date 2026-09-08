## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Namespace 'aiops-case-05' 中缺少 CNI 网络附加定义 'unavailable-network'，导致 Multus 插件无法创建 Pod 沙箱，Pod 持续卡在 ContainerCreating/Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `wait_reason: ContainerCreating` (Fact: `fact-8fcaad83b60f`) | 确认 Pod 处于启动阻塞状态 |
| 2 | K8s Event | Kubernetes | `FailedCreatePodSandBox`: `failed to setup network for sandbox ... plugin type="multus" name="multus-cni-network" failed (add): Multus: ... error in getting k8s network for pod: GetNetworkDelegates: failed getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (Fact: `fact-026a0d8d1b02`) | 核心证据，Kubelet 因 Multus 调用失败导致无法创建容器网络 |
| 3 | K8s Event | Kubernetes | `NoNetworkFound`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` (Fact: `fact-b29c92230b65` 及聚合事实 `fact-026a0d8d1b02`) | 核心证据，Multus 组件报错确认所需的 NetworkAttachmentDefinition 资源不存在 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason="ContainerCreating", value=1) (Fact: `fact-c2604fade993`) | 量化佐证 Pod 处于持续等待状态 |

**证据说明：**
Kubernetes 状态和 Metric 显示 Pod 处于持续等待状态；Kubelet 报错 `FailedCreatePodSandBox` 直接指向网络插件 `multus` 调用失败，而 `NoNetworkFound` 事件明确解释了失败原因为缺少名为 `unavailable-network` 的 `network-attachment-definition` 资源。Metric 与 Event 数据相互印证了 Pod 的状态持续性。

## 🎯 根因分析 · g1

### 因果链

```text
Namespace "aiops-case-05" 中缺少 NetworkAttachmentDefinition "unavailable-network" 资源 → Multus CNI 插件无法解析并挂载网络委托 → Kubelet 创建 Pod 沙箱时网络初始化失败 → Pod 持续处于 ContainerCreating 状态
```

### 根因结论

已确认根因为：**Pod 依赖的 CNI 网络定义资源缺失**。

具体而言，Pod `aiops-case-05/workload-5dbb5dcd6c-kbwsx` 在调度过程中请求使用 Multus 插件挂载网络 `unavailable-network`。然而，在对应命名空间 `aiops-case-05` 中并未找到该网络附加定义（NetworkAttachmentDefinition）。这一缺失直接导致 Multus 插件调用失败，进而阻止了 Pod 沙箱（Container Sandbox）的创建，最终表现为 Pod 无限期处于 `ContainerCreating` 状态。

证据支撑：
- **直接缺失证据**：`NoNetworkFound` 事件（Fact #3）明确指出找不到指定的网络定义资源。
- **失败表现证据**：`FailedCreatePodSandBox` 事件（Fact #2）记录了具体的网络配置失败堆栈。
- **持续状态证据**：`ContainerCreating` 状态（Fact #1, #4）表明该阻塞是持续且非瞬时的。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 27.8s
├─ 并发证据采集: 40.4s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 40.4s (Evidence 34.9s, RCA 5.4s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-imagepull-failed, pod-sandbox-create-failed, pod-volume-mount-failed, pod-config-error
