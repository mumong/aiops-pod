## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod 引用了命名空间 'aiops-case-05' 中不存在的 Multus NetworkAttachmentDefinition 'unavailable-network'，导致 Multus 插件无法发现网络定义，进而引发 FailedCreatePodSandBox，致使 Pod 持续处于 Pending/ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning NoNetworkFound ... 89s ... multus ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` | 直接定位 Multus 插件因找不到网络定义而反复报错 |
| 2 | K8s State | Kubernetes | `container: "app", reason: "ContainerCreating"` | 确认 Pod 卡在容器创建阶段，与事件日志的阻塞状态一致 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1` | 监控指标确认容器处于持续等待状态 |

**证据互证说明：**
Kubernetes 事件（#1）提供了具体的失败原因（Multus 找不到 `unavailable-network`），状态（#2）与指标（#3）共同印证了 Pod 因该原因导致的持续阻塞。由于 Pod 未能启动，未产生日志与链路追踪数据。

## 🎯 根因分析 · g1

### 因果链

```text
Multus 找不到网络定义 → Pod 沙箱创建失败 → 容器处于 ContainerCreating 状态 → Pod 处于 Pending/ContainerCreating 状态
```

### 根因结论

已确认根因：Pod `aiops-case-05/workload-5dbb5dcd6c-nhd7v` 引用了一个不存在的 Multus `NetworkAttachmentDefinition` ('unavailable-network')。

依据证据 **#1** (K8s Event)，Multus 插件反复报出 `"network-attachment-definitions.k8s.cni.cncf.io \"unavailable-network\" not found"` 错误。这一缺失的配置导致 Pod 的底层沙箱无法创建，从而使容器始终停留在 **ContainerCreating** 状态（依据证据 **#2** 和 **#3**）。

---

## 📊 性能统计

```text
├─ 总耗时: 6.3m
├─ 问题定位: 21.6s
├─ 并发证据采集: 348.3s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 348.3s (Evidence 342.5s, RCA 5.6s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed
