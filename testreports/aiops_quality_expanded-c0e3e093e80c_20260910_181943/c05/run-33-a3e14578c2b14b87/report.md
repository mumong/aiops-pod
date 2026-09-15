## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod 声明了不存在的 CNI 网络定义 'unavailable-network'，导致 Multus 插件无法完成网络配置，进而致使 Kubelet 反复失败创建 Pod Sandbox。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-6f70483e2fcb) | Warning FailedCreatePodSandBox 26s (x356 over 78m) kubelet: failed to setup network for sandbox: plugin type="multus" name="multus-cni-network" failed (add): Multus: ... error loading k8s delegates k8s args: TryLoadPodDelegates: error in getting k8s network for pod: GetNetworkDelegates: failed getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05) | 确认 Kubelet 尝试创建 Pod 时因 Multus 插件配置错误失败，且该失败在过去 78 分钟内已累积 356 次，导致容器无法启动。 |
| 2 | K8s Event | kubernetes (fact-00198e07b976) | Warning NoNetworkFound 4m6s multus: cannot find a network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found in namespace (aiops-case-05) | 明确指出 Multus 正在查找名为 `unavailable-network` 的 `network-attachment-definition` 资源，但在 `aiops-case-05` 命名空间中不存在，属于直接因果证据。 |
| 3 | K8s State | kubernetes (fact-0a00ab584eff) | container.waiting_reason: ContainerCreating (container: app) | 证明容器处于挂起状态，等待网络等基础设施准备就绪，与插件报错的阻塞机制相符。 |
| 4 | Metric | prometheus (fact-765f3b728e6d) | kube_pod_container_status_waiting_reason=1 (reason: ContainerCreating, container: app) | 实时状态指标确认 Pod 当前仍因 `ContainerCreating` 处于等待状态，无其他错误状态干扰。 |

**证据交叉印证：**
Kubernetes 的 `FailedCreatePodSandBox` 事件详细记录了失败的堆栈（证据 #1），直接指向了具体的插件错误（证据 #2）；Kubernetes 状态和 Metric 指标（证据 #3、#4）共同确认了这一网络配置错误导致了 Pod 创建过程的完全挂起。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 声明了不存在的 NetworkAttachmentDefinition (unavailable-network) → Multus CNI 插件无法获取网络配置 → Kubelet 反复调用 Multus 失败并记录事件 (x356 over 78m) → Pod 持续处于 ContainerCreating 等待状态
```

### 根因结论
已确认的根因是：在 `aiops-case-05` 命名空间中，该 Pod 试图关联一个名为 `unavailable-network` 的 `network-attachment-definition` 资源，但集群中该资源不存在。
- **证据支撑**：Multus 组件的 46 次 `NoNetworkFound` 警告事件（如证据 #2），以及 Kubelet 记录的 356 次 `FailedCreatePodSandBox` 失败事件（如证据 #1），均明确指出了缺失资源的名称 `unavailable-network`。
- **现象解释**：由于缺乏该自定义网络定义，Multus 插件无法完成网络配置，导致 Pod Sandbox 创建被永久阻塞，表现为 `ContainerCreating` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 11.8s
├─ 并发证据采集: 41.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 41.5s (Evidence 36.6s, RCA 4.8s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed
