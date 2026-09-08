## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx (aiops-case-05) 处于 Pending 状态，Container 状态为 Waiting (reason: ContainerCreating)。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-011d57a35376` | FailedCreatePodSandBox (x311 over 71m)：`failed to setup network for sandbox ... plugin type="multus" name="multus-cni-network" failed (add): ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 直接展示 kubelet 在创建沙箱时的网络配置失败堆栈，指向 Multus 插件找不到指定网络。 |
| 2 | K8s Event | `fact-005f3ac6823a` | NoNetworkFound (32m)：`cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` | 佐证 Pod 注解中引用的 `unavailable-network` 资源在集群中确实不存在。 |
| 3 | K8s State | `fact-578efeff6029` | `container.waiting_reason`：`ContainerCreating` | 反映当前 Pod 的实际运行状态，处于等待网络初始化的挂起阶段。 |
| 4 | Metric | `fact-34cd265ed6d8` | `kube_pod_container_status_waiting_reason` (reason=ContainerCreating)：1 | 确认当前只有一个 Pod 实例呈现该状态，无大规模集群级蔓延。 |

**证据说明：**
K8s Event 中的 `FailedCreatePodSandBox` 和 `NoNetworkFound` 错误信息高度一致，均明确指向 Multus CNI 无法解析 `aiops-case-05` 命名空间下的 `unavailable-network` 资源。`container.waiting_reason` 和 Prometheus Metric 进一步确认了这一状态是持续的（持续 71 分钟）且针对该特定工作负载实例。日志与追踪数据因容器未启动而缺失，但 Kubernetes 控制面的事件与状态已足以闭环诊断。

## 🎯 根因分析 · g1

### 因果链

```text
NetworkAttachmentDefinition CR 'unavailable-network' 缺失 → Multus CNI 插件无法获取网络配置返回 NoNetworkFound 错误 → kubelet 调用 container runtime 创建沙箱失败 (FailedCreatePodSandBox) → Pod 停留在 Pending 阶段，容器状态为 ContainerCreating
```

### 根因结论

**已确认根因：**
Pod `aiops-case-05/workload-5dbb5dcd6c-kbwsx` 的 Multus CNI 注解引用了一个名为 `unavailable-network` 的 `NetworkAttachmentDefinition` 资源，但该自定义资源（CR）在 `aiops-case-05` 命名空间中并不存在。这导致 Multus 插件在初始化网络时无法找到配置定义，直接报错 `NoNetworkFound`，进而使 kubelet 无法成功创建 Pod 网络沙箱，最终导致 Pod 卡死在 `ContainerCreating` 状态。

**证据支撑：**
- **错误原文一致性**：K8s Event `fact-005f3ac6823a` 与 `fact-011d57a35376` 均明确报告了“cannot find a network-attachment-definition ... 'unavailable-network' ... not found”，排除了网络插件配置错误或运行时故障的可能性，直指资源缺失。
- **状态匹配**：Pod 状态 `ContainerCreating` 与 `FailedCreatePodSandBox` 错误完全吻合，表明阻塞点就在容器启动前的网络准备阶段。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.0s
├─ 并发证据采集: 47.9s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 47.9s (Evidence 38.3s, RCA 9.4s)
└─ 汇总总结: 12.3s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-sandbox-create-failed
