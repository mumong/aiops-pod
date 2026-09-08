## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-nhd7v 停留在 ContainerCreating 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: container "app" reason "ContainerCreating" | 确认 Pod 当前处于未就绪的等待状态，直接支撑异常现象 |
| 2 | K8s Event | multus | `NoNetworkFound`: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05) | 揭示 Multus CNI 插件在配置网络时，无法在目标命名空间下找到 Pod 声明引用的 `unavailable-network` 定义，是导致网络插件失败的核心上游原因 |
| 3 | K8s Event | kubelet | `FailedCreatePodSandBox`: failed to setup network for sandbox ... plugin type="multus" ... GetNetworkDelegates: failed getting the delegate | 确认 kubelet 底层沙箱创建过程中因 Multus 网络配置获取失败而被阻断，形成了从网络缺失到沙箱创建报错的因果闭环 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: 值 1, reason "ContainerCreating" (sample_count: 1) | 辅助确认 Pod 持续处于 Waiting 状态，但由于单样本且趋势不可评估，不作为主导诊断依据，主要与 K8s Event 互相印证 Pod 未能进入运行态 |

**证据印证说明：**
1. **状态与事件匹配**：K8s State 中的 `ContainerCreating` 状态与 Event 中反复出现的 `FailedCreatePodSandBox` 直接对应，表明该 Pod 处于网络配置重试或阻塞阶段。
2. **根因明确**：所有 `FailedCreatePodSandBox` 事件的报错原因均指向同一个网络定义 `unavailable-network` 的缺失，且 Multus 的 `NoNetworkFound` 事件持续高频上报，排除了其他网络组件或资源不足的可能性。
3. **数据维度补充**：Metric 数据虽确认了等待状态，但由于单样本且与 K8s Event 表现出的明确报错机制存在维度冗余，故主要依赖 Event 作为根因分析的决定性依据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 引用不存在的 NetworkAttachmentDefinition 'unavailable-network' → Multus 插件无法获取并配置网络资源 → kubelet 创建 Pod 沙箱 (sandbox) 失败 → Pod 停留在 ContainerCreating 状态
```

### 根因结论

**已确认的根因**：
异常组 `g1` 的故障根因为 **Pod 规范声明的网络依赖缺失**。

具体而言，在命名空间 `aiops-case-05` 下的 Pod `workload-5dbb5dcd6c-nhd7v` 的规范中，引用了一个名为 `unavailable-network` 的 `NetworkAttachmentDefinition`（通过证据 #2 中的 Multus 事件确认）。然而，该网络定义在对应命名空间中并未实际存在，导致 CNI 插件 Multus 无法为其配置网络接口，进而引起 kubelet 持续报出 `FailedCreatePodSandBox` 错误（证据 #3），最终造成 Pod 无法启动并一直卡在 `ContainerCreating` 状态（证据 #1、#4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 25.1s
├─ 并发证据采集: 47.1s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 47.1s (Evidence 37.3s, RCA 9.7s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed
