## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-bntfh stuck in ContainerCreating (Pending) state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `event.message` | `NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` (fact-00b03486d720) | 证明 Multus CNI 插件持续报告找不到特定网络资源，且该错误已在 50 分钟窗口内高频复现。 |
| 2 | K8s Event | `event.message` | `FailedCreatePodSandBox ... Failed to create pod sandbox: rpc error: code = Unknown desc = failed to setup network for sandbox ... Multus ... error loading k8s delegates k8s args ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` (fact-344c1fdfbd1b) | 证明底层 kubelet 因上述网络插件失败导致 Pod 沙箱创建彻底失败（x425），这是 Pod 停滞的直接技术原因。 |
| 3 | K8s State | `container.waiting_reason` | `Container: app, Reason: ContainerCreating` (fact-b7c41df84fa5) | 确认 Pod 当前处于等待网络初始化的停滞状态，状态与实际错误原因（网络依赖缺失）一致。 |
| 4 | Metric | `kube_pod_container_status_waiting_reason` | `container="app", reason="ContainerCreating", value=1, sample_count=1` (fact-9807727f71d7) | 提供客观指标证明该容器当前正等待处于 `ContainerCreating` 状态，支撑异常状态的持续性。 |

**证据综合说明**：K8s 事件（#1, #2）与状态指标（#3, #4）相互印证，明确显示了从 "Multus 找不到资源" 到 "沙箱创建失败" 再到 "Pod 停滞" 的完整因果链，所有证据均指向同一个网络资源缺失的问题。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用不存在的网络资源 → Multus CNI 初始化失败 → kubelet 创建沙箱 RPC 调用被拒 → Pod 卡在 ContainerCreating 状态
```

### 根因结论

已确认根因为 **命名空间 `aiops-case-05` 中引用了名为 `unavailable-network` 的 Multus NetworkAttachmentDefinition (NAD)，但该资源在集群中不存在**。

*   **事实支撑**：Kubernetes 事件日志 `fact-00b03486d720` 和 `fact-344c1fdfbd1b` 明确记录了 `NoNetworkFound` 及 `cannot find a network-attachment-definition (unavailable-network)` 错误。
*   **结论逻辑**：Pod 配置中的网络注解指向了不存在的自定义网络资源，导致负责网络配置的 Multus 插件无法完成沙箱的网络设置，进而被 kubelet 中止并反复重试，表现为 Pod 长期处于 `ContainerCreating` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 6.4m
├─ 问题定位: 21.9s
├─ 并发证据采集: 348.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 348.5s (Evidence 341.2s, RCA 7.2s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed
