## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod spec 中引用的 NetworkAttachmentDefinition 'unavailable-network' 在 namespace 'aiops-case-05' 中不存在，导致 Multus CNI 插件在创建 Pod 沙箱时反复失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `Waiting Reason: ContainerCreating` (`fact-ef96d9c92fa4`) | 确诊容器处于启动停滞状态，等待基础设施就绪。 |
| 2 | K8s State | Kubernetes | `Pod Phase: Pending` (`fact-bf1b01a0b9dd`) | 证实 Pod 尚未进入运行阶段，调度或前置准备受阻。 |
| 3 | K8s Config | Kubernetes | `NetworkAttachmentDefinition 'unavailable-network' not found` (诊断信息) | 直接锁定根因：Pod Spec 中引用的网络定义缺失，导致 Multus CNI 无法配置网络。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason = 1` (reason: ContainerCreating) (`fact-051c8472eb1f`) | 指标层面验证了容器持续卡在 ContainerCreating 状态的事实。 |

**证据说明**：
Kubernetes 状态显示 Pod 持续处于 `Pending` 且容器等待原因为 `ContainerCreating`，指标数据 (`fact-051c8472eb1f`) 在观测时间窗内持续反映该状态。由于容器尚未启动，Logging 和 Tracing 维度客观上无法采集数据，这与“容器未启动”的现象相符。核心证据指向 K8s 配置检查发现的 `NetworkAttachmentDefinition` 缺失，解释了 CNI 插件为何无法完成沙箱创建。

## 🎯 根因分析 · g1

### 因果链

```text
NetworkAttachmentDefinition 'unavailable-network' 定义缺失 → Multus CNI 无法解析网络配置并创建 Pod 沙箱 → 容器状态持续为 ContainerCreating → Pod 保持 Pending 状态
```

### 根因结论

已确认的根因是 **网络配置引用错误**：Pod 的 Spec 中配置了 `NetworkAttachmentDefinition 'unavailable-network'`，但在当前命名空间 `aiops-case-05` 中该资源不存在。这导致 Multus CNI 插件在初始化网络时反复失败，表现为 Pod 状态始终处于 `Pending`，容器状态为 `ContainerCreating`（证据见 `fact-051c8472eb1f` 及诊断信息）。

---

## 📊 性能统计

```text
├─ 总耗时: 59.4s
├─ 问题定位: 15.3s
├─ 并发证据采集: 36.3s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 36.3s (Evidence 30.7s, RCA 5.5s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed, pod-sandbox-create-failed
