## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod workload-5dbb5dcd6c-bntfh stuck in ContainerCreating (Pending) due to Multus CNI failure |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `ContainerCreating` | 确认 Pod 当前卡在初始化阶段，未进入 Running 状态 |
| 2 | K8s Event | multus | `NoNetworkFound`: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05) | 提供持续性的失败原因，指向特定的资源名称缺失 |
| 3 | K8s Event | kubelet | `FailedCreatePodSandBox`: error loading k8s delegates ... failed getting the delegate ... not found | 从 Pod 调度器视角证实网络插件初始化失败是导致沙箱创建失败的根本机制 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (reason="ContainerCreating", value="1") | 指标确认当前等待原因与 Kubernetes 事件状态一致 |

**证据分析**：
Kubernetes 状态确认了 Pod 的停滞位置。Multus 事件与 kubelet 错误高度印证，错误原文精确指出了缺失的 `NetworkAttachmentDefinition` 资源名为 `unavailable-network`。Metric 数据仅提供了状态值的量化确认，未改变定性结论。由于 Pod 无法启动，Logging 和 Tracing 维度无数据。

## 🎯 根因分析 · g1

### 因果链

```text
未找到资源 'unavailable-network' → Multus 无法解析网络配置 → Pod 沙箱创建失败 → 状态卡在 ContainerCreating
```

### 根因结论

已确认的根因是 Pod 所在的 `aiops-case-05` 命名空间中引用了一个名为 `unavailable-network` 的 `NetworkAttachmentDefinition`，但该资源不存在（证据 #2, #3）。Multus 插件在尝试挂载网络时因找不到该定义而抛出错误，导致 kubelet 无法创建 Pod 沙箱，进而使 Pod 永久停留在 `ContainerCreating` 状态。

缺少关于该资源为何不存在的事实（如是否被误删或拼写错误），但这不影响当前故障现象的诊断。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.5s
├─ 并发证据采集: 51.1s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 51.1s (Evidence 40.2s, RCA 10.7s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed
