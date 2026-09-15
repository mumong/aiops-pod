## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod workload-5dbb5dcd6c-bntfh in namespace aiops-case-05 stuck in ContainerCreating/Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: container="app", reason="ContainerCreating" | 确认容器处于启动等待阶段，尚未运行。 |
| 2 | K8s Event | multus (kubelet) | `FailedCreatePodSandBox`: failed to setup network for sandbox "1861e3...": plugin type="multus" name="multus-cni-network" failed (add): Multus: ... error in getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05) | 记录 kubelet 创建 Pod 沙箱时的核心失败机制，直接指向 Multus 插件无法加载网络配置。 |
| 3 | K8s Event | multus | `NoNetworkFound`: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found (连续出现 46 次，跨度 3 分钟至 60 分钟) | 持续证实 Pod 请求的网络资源在指定命名空间中不存在，排除临时网络波动。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (container="app", reason="ContainerCreating"): 1 | 从监控维度确认等待状态为持续性，无自愈迹象。 |

**证据综合分析**：
Kubernetes 状态与 Multus 事件形成直接因果印证：容器因网络沙箱创建失败而卡在 `ContainerCreating`（证据 1、4）；底层原因确认为 `multus-cni-network` 插件在调用时，在 `aiops-case-05` 命名空间中查不到名为 `unavailable-network` 的 NetworkAttachmentDefinition 对象（证据 2、3）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用不存在的网络定义 → Multus CNI 插件无法找到配置并失败 → kubelet 创建沙箱失败 → Pod 持续卡在 ContainerCreating 状态
```

### 根因结论

已确认的根因为：Pod 依赖的 Multus 网络附件定义 `unavailable-network` 在命名空间 `aiops-case-05` 中缺失。

**分析依据**：
1. **K8s Event 证据 (NoNetworkFound, FailedCreatePodSandBox)**：明确且连续地指出了 Multus 插件在尝试解析 Pod 网络配置时，找不到指定的 `network-attachment-definitions` 对象，这是导致无法创建网络沙箱的直接原因。
2. **K8s State 证据 (ContainerCreating)**：证实了 Pod 因上述网络插件失败而无法进入运行状态。

综上，Pod 启动阻塞的根本原因是配置错误（引用了不存在的资源），而非集群网络故障或调度问题。

---

## 📊 性能统计

```text
├─ 总耗时: 6.4m
├─ 问题定位: 18.6s
├─ 并发证据采集: 352.4s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 352.4s (Evidence 345.0s, RCA 7.2s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-imagepull-failed
