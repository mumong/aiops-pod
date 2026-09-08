## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v 长期处于 Pending 状态，ContainerCreating 阶段失败，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.waiting_reason = "ContainerCreating" (container: app) | 确认 Pod 处于等待网络分配的中间状态 [fact-c6f9807b552b] |
| 2 | K8s Event | Kubernetes | FailedCreatePodSandBox: "failed to setup network for sandbox ... plugin type=\"multus\" ... error in getting k8s network for pod: GetNetworkDelegates: failed getting the delegate" | 明确指出网络沙箱创建失败，根源在于 Multus 获取 Delegate 配置失败 [fact-10f47afe4dc0] |
| 3 | K8s Event | Kubernetes | NoNetworkFound: "cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io \"unavailable-network\" not found" (重复 46 次) | 具体确认导致 Delegate 获取失败的原因是 Namespace "aiops-case-05" 中不存在名为 "unavailable-network" 的 CRD 资源 [fact-10af22077646] |
| 4 | Metric | Prometheus | kube_pod_container_status_waiting_reason = 1 (container: app, reason: ContainerCreating, timestamp: 2026-09-03T11:50:23Z) | 从监控指标侧面印证 Pod 长期处于 ContainerCreating 状态 [fact-e0c9ea04212b] |

**证据说明**：
1. **K8s 事件与状态互证**：Pod 状态 `ContainerCreating` 与 `FailedCreatePodSandBox` 错误同步存在，表明问题发生在容器启动前的网络准备阶段。
2. **根因锁定**：多次重复的 `NoNetworkFound` 事件（fact-10af22077646 等）与 `FailedCreatePodSandBox` 的根本原因描述（fact-10f47afe4dc0）高度一致，确认为配置引用了一个不存在的资源。
3. **其他维度受限**：由于 Pod 未能启动（`container_status_waiting_reason=1`），Logging 和 Tracing 维度物理上无法采集到应用数据，证据链完全由 Kubernetes 基础设施状态支撑。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了 Namespace 'aiops-case-05' 中不存在的 NetworkAttachmentDefinition 'unavailable-network' (fact-10af22077646)
→
Multus CNI 插件在初始化网络时无法通过 'GetNetworkDelegates' 获取有效的网络 Delegate 配置
→
kubelet 创建 Pod 沙箱（SandBox）失败，持续抛出 "failed to setup network for sandbox" 错误 (fact-10f47afe4dc0)
→
Pod 无法完成初始化，长期卡在 ContainerCreating 状态 (fact-c6f9807b552b, fact-e0c9ea04212b)
```

### 根因结论

**已确认的根因**：
Pod `workload-5dbb5dcd6c-nhd7v` 的配置中引用了一个名为 `unavailable-network` 的网络附加定义，但该定义在对应的 Namespace `aiops-case-05` 中不存在。

这一缺失直接导致 Multus CNI 插件在尝试配置 Pod 网络时无法找到对应的 Delegate 资源，进而引发 Pod 沙箱创建失败。证据链中 `NoNetworkFound` 事件的极高重复频率与 `FailedCreatePodSandBox` 的错误堆栈相互印证，结论确定性高。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 22.0s
├─ 并发证据采集: 47.9s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 47.9s (Evidence 38.8s, RCA 8.8s)
└─ 汇总总结: 12.7s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed
