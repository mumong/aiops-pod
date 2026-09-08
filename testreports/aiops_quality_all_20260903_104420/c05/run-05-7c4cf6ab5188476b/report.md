## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod `workload-5dbb5dcd6c-nhd7v` 配置了 Multus CNI 所需的 `NetworkAttachmentDefinition` 资源 'unavailable-network'，但该资源在命名空间 `aiops-case-05` 中缺失，导致 kubelet 无法创建 Pod 沙箱。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: ContainerCreating | 确认 Pod 当前卡在容器创建阶段，未进入运行态。 |
| 2 | K8s Config | Kubernetes | `container.resource_request.cpu`: 5m / `container.resource_limit.cpu`: 50m / `memory_request`: 8Mi / `memory_limit`: 32Mi | 排除资源配额不足导致调度或启动失败的可能。 |
| 3 | K8s Event | Kubernetes | `NoNetworkFound`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 直接证明 Multus CNI 在命名空间中找不到 Pod 依赖的网络插件定义。 |
| 4 | K8s Event | Kubernetes | `FailedCreatePodSandBox`: `failed to setup network... plugin type="multus" name="multus-cni-network" failed (add)` | 证实 kubelet 尝试创建沙箱时因 Multus 插件报错而彻底失败。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason`: 1 (reason: ContainerCreating, sample_count: 1) | 独立于事件日志，通过指标确认容器处于等待状态。 |

**证据链印证**：Kubernetes 指标确认了“等待”的状态，而重复出现的 `NoNetworkFound` 事件和 `FailedCreatePodSandBox` 事件从机制上锁定了失败原因。K8s 配置证实资源请求极小，排除了资源竞争，进一步将焦点集中于网络配置这一单一故障点。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了名为 'unavailable-network' 的 NetworkAttachmentDefinition 引用 → Multus CNI 在命名空间 aiops-case-05 中查找该资源未找到 (NoNetworkFound) → kubelet 无法执行网络插件初始化导致 Pod Sandbox 创建失败 (FailedCreatePodSandBox) → Pod 状态持续卡在 ContainerCreating (见 fact-3, fact-4, fact-1)
```

### 根因结论

已确认根因为**配置性错误**：Pod `aiops-case-05/workload-5dbb5dcd6c-nhd7v` 声明依赖 `NetworkAttachmentDefinition` 资源 `unavailable-network`，但在该命名空间内该资源不存在（见证据 3）。这导致 Multus CNI 插件无法完成网络配置，进而引发 kubelet 创建沙箱失败（见证据 4）。证据链逻辑闭环完整，无需更多诊断数据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 35.0s
├─ 并发证据采集: 52.8s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 52.8s (Evidence 43.8s, RCA 8.8s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-sandbox-create-failed, pod-imagepull-failed, pod-volume-mount-failed
