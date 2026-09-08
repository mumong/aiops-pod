## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v stuck in ContainerCreating/Pending due to Multus CNI sandbox creation failure. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`：container=app, reason=ContainerCreating | 确认应用容器当前处于未就绪状态 |
| 2 | K8s Event | kubernetes | 多次 `NoNetworkFound` (46次)，message: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` | 证明 Multus 持续因找不到特定 NAD 配置而报错，是引发 Pod 卡住的核心原因 |
| 3 | K8s Event | kubernetes | `FailedCreatePodSandBox`，message: `error loading k8s delegates k8s args: ... GetNetworkDelegates: failed getting the delegate: ... "unavailable-network" not found` | 确认 kubelet 试图创建沙箱时，被 Multus 插件直接阻断 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (1) | 指标确认 Pod 处于 ContainerCreating 等待状态，但单样本无法体现趋势 |

**证据小结：**
K8s 状态与 Metrics 共同证实容器卡在 `ContainerCreating` 阶段。多条 K8s Event 证据（#2, #3）完全一致地指向根本原因：Multus 插件在初始化网络时，因为找不到名称为 `unavailable-network` 的 `NetworkAttachmentDefinition` 对象而反复失败，导致 Pod 无法创建网络沙箱。Logging 和 Tracing 因容器未启动而不适用。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了名为 'unavailable-network' 的 NAD (未确认是否为拼写错误) → Multus 插件在沙箱创建时尝试加载该网络委托失败 → 返回 NoNetworkFound 错误 → Pod 无法建立网络沙箱，卡在 ContainerCreating 状态
```

### 根因结论

已确认的根因是 **Pod 规范引用了一个在 `aiops-case-05` 命名空间中不存在的 `NetworkAttachmentDefinition` (`unavailable-network`)**。
*   **机制验证**：K8s 事件显示 Multus 插件反复尝试处理网络配置并失败（证据 #2, #3）。
*   **直接后果**：由于网络插件初始化失败，kubelet 无法创建 Pod 沙箱，导致容器被标记为 `ContainerCreating` 且长期挂起（证据 #1, #4）。
*   **不确定性**：目前无法确知 `unavailable-network` 是应用配置中的拼写错误，还是确实遗漏了部署对应的 NAD 资源。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 28.9s
├─ 并发证据采集: 58.1s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 58.1s (Evidence 49.1s, RCA 8.9s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed, pod-imagepull-failed, pod-sandbox-create-failed
