## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-kbwsx stuck in ContainerCreating/Pending |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning NoNetworkFound 40s multus cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` [fact-48214a15dffc] | 直接指出缺失特定 CNI 配置对象 |
| 2 | K8s Event | Kubernetes | `Warning FailedCreatePodSandBox 52m kubelet Failed to create pod sandbox: ... failed to setup network ... cannot find a network-attachment-definition (unavailable-network)` [fact-5dcc30b1dd6f] | 确认 Multus 插件因网络配置缺失导致沙箱创建失败 |
| 3 | K8s State | Kubernetes | `container.waiting_reason`: reason=ContainerCreating [fact-e79d84880c25] | 确认容器处于等待网络的阻塞状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 计数为 1，原因 `ContainerCreating`，样本数 1，无趋势数据 [fact-c92d8e3fe8fa] | 独立确认 Pod 卡在初始化阶段的等待状态 |

**证据说明：**
Kubernetes 事件日志中重复出现的 `NoNetworkFound` 警告与 `FailedCreatePodSandBox` 错误一致指向 `network-attachment-definition` 查找失败（[1], [2]）。该事件直接解释了 `K8s State` 中的 `ContainerCreating` 状态 [3] 以及 `Metric` 中的等待计数 [4]。由于容器未能启动，Logging 和 Tracing 均为空，诊断完全依赖于 Kubernetes 事件与状态事实。

## 🎯 根因分析 · g1

### 因果链

```text
缺少 CRD: NetworkAttachmentDefinition 'unavailable-network' in namespace 'aiops-case-05' → 
Multus CNI 无法获取 Pod 网络配置 → 
Failed to create pod sandbox (网络设置失败) → 
Pod aiops-case-05/workload-5dbb5dcd6c-kbwsx 持续处于 ContainerCreating/Pending 状态
```

### 根因结论

已确认的根因是：Pod 的 `aiops-case-05` 命名空间中不存在 `NetworkAttachmentDefinition` 资源 `unavailable-network`，导致 Multus CNI 插件无法完成网络配置，进而使 `kubelet` 无法创建 Pod 沙箱 [2]。该结论由 K8s 事件 [1, 2]、状态 [3] 及指标 [4] 相互印证。

尚未确认的缺陷是：`unavailable-network` 对象缺失的具体原因（例如是否拼写错误、配置未部署或遭误删），缺乏对该资源生命周期或配置来源的验证数据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 39.2s
├─ 并发证据采集: 55.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 55.5s (Evidence 46.6s, RCA 8.7s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed, pod-imagepull-failed, pod-sandbox-create-failed
