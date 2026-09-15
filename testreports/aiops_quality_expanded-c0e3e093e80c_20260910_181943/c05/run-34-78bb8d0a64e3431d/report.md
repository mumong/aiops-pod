## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-bntfh 被配置了 annotation k8s.v1.cni.cncf.io/networks=unavailable-network，但该 namespace (aiops-case-05) 下不存在对应的 NetworkAttachmentDefinition 资源（unavailable-network）。Multus CNI 插件因无法找到该网络定义而报错 'NoNetworkFound'，导致容器沙箱创建失败（FailedCreatePodSandBox），Pod 卡在 Pending/ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: reason=`ContainerCreating` | 确认 Pod 当前异常状态及停滞阶段。 |
| 2 | K8s Event | Kubernetes | `FailedCreatePodSandBox`: `rpc error: ... plugin type="multus" ... error loading k8s delegates ... getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 直接揭示底层容器沙箱创建失败的具体机制及缺失资源名称。 |
| 3 | K8s Event | Kubernetes | `NoNetworkFound`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 确认 Multus 插件在指定命名空间内查无目标网络定义，且该错误在 80m 时间窗内高频出现（46次以上），非偶发现象。 |

**证据说明：**
1. Kubernetes 的 `ContainerCreating` 等待状态（行 1）由底层沙箱创建失败（行 2）导致。
2. 行 2 的 `FailedCreatePodSandBox` 报错明确指出 `multus` 插件在尝试加载 `k8s` 委派网络时失败，根本原因是无法获取网络定义。
3. 行 3 的 `NoNetworkFound` 事件进一步锁定具体缺失的资源为 `network-attachment-definitions.k8s.cni.cncf.io "unavailable-network"`，与行 2 的失败机制完全一致，形成闭环证据链。Metric/Logging/Tracing 维度因 Pod 未启动或无相关数据，不作为该配置错误的支撑证据。

## 🎯 根因分析 · g1

### 因果链
```text
缺失 NetworkAttachmentDefinition 资源 → Multus CNI 插件无法获取网络委派配置 → 容器沙箱创建失败 (FailedCreatePodSandBox) → Pod 卡在 ContainerCreating 状态
```

### 根因结论
**已确认的根因**：Pod `aiops-case-05/workload-5dbb5dcd6c-bntfh` 配置了网络注解 `k8s.v1.cni.cncf.io/networks=unavailable-network`，要求 Multus 插件接入名为 `unavailable-network` 的网络，但在 `aiops-case-05` 命名空间中不存在对应的 `NetworkAttachmentDefinition` 资源。

**证据引用**：
- 该根因由 K8s Event 直接证实：Multus 插件多次报告 `NoNetworkFound`（#3），并伴随底层 `kubelet` 报告的 `FailedCreatePodSandBox` 错误（#2）。
- 现象与状态完全吻合：Pod 因此卡在 `ContainerCreating` 状态（#1）。
- 缺失决定性事实：无。Kubernetes 控制平面提供的 Event 和 State 事实已充分证明资源缺失与故障之间的直接因果关系。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 24.2s
├─ 并发证据采集: 54.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 54.5s (Evidence 47.7s, RCA 6.7s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-sandbox-create-failed
