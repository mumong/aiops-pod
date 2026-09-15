## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-bntfh 持续处于 ContainerCreating (Pending) 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `NoNetworkFound`: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found | 持续报错，证明 Multus 试图加载名为 'unavailable-network' 的 CNI 插件时，在目标命名空间找不到对应的定义对象，这是阻塞 Pod 启动的直接原因 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: reason="ContainerCreating" | 证实 Pod 正处于等待容器网络初始化的阶段，与 CNI 插件加载失败导致沙箱创建停滞的状态一致 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (container: "app", reason: "ContainerCreating") | 指标层面的佐证，当前 Pod 的等待原因为 ContainerCreating，与事件日志中的状态同步 |

**证据关联说明：**
事件日志 (Fact 1) 提供了明确的失败语义（找不到特定 CNI 定义），状态 (Fact 2) 和指标 (Fact 3) 共同证实了 Pod 被卡在网络初始化阶段。由于容器未启动，Logging 和 Tracing 维度的数据不可用，Kubernetes 事件已成为确定根因的唯一事实来源。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义了引用不存在 CNI 定义的网络配置 (unavailable-network) → Multus CNI 插件在 aiops-case-05 命名空间下查找并失败 → Kubelet 调用 CRI 创建容器网络命名空间失败 (RPC Unknown desc) → Pod 持续处于 ContainerCreating 状态
```

### 根因结论

已确认根因为 **Multus CNI 插件缺失配置**。
Pod `aiops-case-05/workload-5dbb5dcd6c-bntfh` 的声明式配置中引用了网络附加定义 `unavailable-network`，但在其所属的 `aiops-case-05` 命名空间中该对象不存在（见证据 1 `fact-037fb4fe4a42`）。这导致 Multus 插件链加载失败，Kubelet 无法完成网络沙箱的创建，从而引发状态 `ContainerCreating` 挂起（见证据 2 `fact-1cb3b4101338`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 25.0s
├─ 并发证据采集: 36.6s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 36.6s (Evidence 28.0s, RCA 8.4s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed
