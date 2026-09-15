## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod workload-5dbb5dcd6c-bntfh 处于 ContainerCreating 状态，无法启动容器 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason` = `ContainerCreating` (`fact-41749809a435`) | 确认 Pod `workload-5dbb5dcd6c-bntfh` 处于容器创建等待阶段，未进入运行态。 |
| 2 | K8s Event | multus | `NoNetworkFound`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` (聚合 46 条，如 `fact-07bc92f2e8a9`) | 核心错误证据：CNI 插件 Multus 在指定命名空间中找不到名称为 `unavailable-network` 的网络定义。 |
| 3 | K8s Event | kubelet | `FailedCreatePodSandBox`: `failed to setup network for sandbox ... plugin type="multus" ... error in getting the delegate ... getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (聚合事实，如 `fact-165e0a6dfcb2`) | 因果闭环：Kubelet 因 Multus 无法配置网络而无法创建 Pod 沙箱，直接导致容器创建失败。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (reason=`ContainerCreating`) 当前值 1 (`fact-f1388645510a`) | 量化佐证：确认目标 Pod 持续处于 Waiting 状态的实时指标观测。 |

**证据关联说明：**
Kubernetes 事件（#2, #3）明确指出失败原因是引用了不存在的 `network-attachment-definition`。Multus 抛出的 `NoNetworkFound` 异常（#2）直接导致 Kubelet 的 `FailedCreatePodSandBox`（#3），这与 Pod 状态和指标观测到的 `ContainerCreating`（#1, #4）完全一致，证实了网络配置缺失是阻塞容器启动的唯一障碍。Logging 与 Tracing 因 Pod 未启动被确认为不适用，无冲突证据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 配置引用 'unavailable-network' (未确认原因) → 命名空间缺少对应 NetworkAttachmentDefinition → Multus CNI 插件抛出 NoNetworkFound 错误 → Kubelet 无法创建 Pod Sandbox → Pod 卡在 ContainerCreating 状态
```

### 根因结论

已确认根因：Pod `aiops-case-05/workload-5dbb5dcd6c-bntfh` 无法启动是由于网络配置错误。Pod 配置引用了一个名为 `unavailable-network` 的 `NetworkAttachmentDefinition`，但在 `aiops-case-05` 命名空间中该资源不存在（证据 #2, #3）。这导致 Multus CNI 插件在初始化网络时无法获取有效的 CNI 插件配置，进而导致 Kubelet 创建沙箱失败。

**缺失信息：**
现有证据仅确认了“配置引用不存在”这一事实，无法解释“为何 YAML 中配置了 `unavailable-network` 而非有效网络”这一上游原因（如配置错误、资源未部署或拼写错误）。

---

## 📊 性能统计

```text
├─ 总耗时: 6.6m
├─ 问题定位: 30.6s
├─ 并发证据采集: 354.2s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 354.2s (Evidence 344.6s, RCA 9.5s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- 未调用 Runbook
