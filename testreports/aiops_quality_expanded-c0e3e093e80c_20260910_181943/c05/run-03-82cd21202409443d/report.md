## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod workload-5dbb5dcd6c-bntfh 处于 ContainerCreating (Pending) 状态，无法启动容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning NoNetworkFound multus cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 明确标识 Multus 插件在创建网络时因找不到指定的 NetworkAttachmentDefinition 资源而失败 |
| 2 | K8s Event | kubernetes | `Warning FailedCreatePodSandBox kubelet Failed to create pod sandbox: ... multus-cni-network failed (add): ... cannot find a network-attachment-definition (unavailable-network)` | 提供因果链的下游证据，证实网络配置错误直接导致 Kubelet 无法初始化 Pod 沙箱环境 |
| 3 | K8s Config | kubernetes | `Annotations: cni.projectcalico.org/networks: unavailable-network` | 提供触发异常的源头事实，确认为 Pod 模板显式配置了名为 "unavailable-network" 的网络定义 |
| 4 | K8s State | kubernetes | `Waiting Reason: ContainerCreating` (Metrics: `kube_pod_container_status_waiting_reason` value=1) | 确认当前异常现象状态，与 CNI 插件报错的容器生命周期阶段一致 |

**证据说明：**
K8s 事件证据 #1 与 #2 从插件端 (multus) 和运行时端 (kubelet) 完整复现了网络初始化失败的因果过程；配置证据 #3 证实了具体的错误配置项，直接支撑了事件报错中的 "unavailable-network" 参数。

## 🎯 根因分析 · g1

### 因果链

```text
缺失 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件无法获取网络委托并报错 → Kubelet 创建 Pod Sandbox 失败 (FailedCreatePodSandBox) → Pod 停留在 ContainerCreating 状态
```

### 根因结论

已确认的根因为：Pod `aiops-case-05/workload-5dbb5dcd6c-bntfh` 的模板中引用了不存在的 NetworkAttachmentDefinition 资源 `unavailable-network`（由事实 #3 确认）。这导致 Multus 插件在尝试配置网络时发生 `NoNetworkFound` 错误（事实 #1），进而导致 Kubelet 无法建立网络沙箱，引发 `FailedCreatePodSandBox`（事实 #2），最终表现为 Pod 状态停滞在 `ContainerCreating`。

未确认项：
- 部署该 Pod 的团队为何配置了该网络资源，以及该资源确切的预期命名空间（当前配置位于 `aiops-case-05`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 18.9s
├─ 并发证据采集: 49.0s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 49.0s (Evidence 40.0s, RCA 8.8s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed
