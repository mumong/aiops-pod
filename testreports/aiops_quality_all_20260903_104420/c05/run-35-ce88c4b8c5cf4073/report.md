## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v stuck in ContainerCreating (Pending) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning NoNetworkFound ... multus cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` (聚合 47 条，持续时间约 60 分钟) | 直接证实 Multus CNI 因找不到指定的 NetworkAttachmentDefinition 而持续报错 |
| 2 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = `ContainerCreating` (当前值 `1`) | 确认 Pod 当前处于等待容器启动的状态，与事件中的 CNI 报错原因一致 |

**证据说明**：Kubernetes 事件提供了详细的错误文本（47 次重复），明确指出 `multus` 插件无法在 `aiops-case-05` 命名空间中解析 `unavailable-network` 这一网络定义；Prometheus 指标进一步印证了 Pod 停留在 `ContainerCreating` 阶段，且没有其他等待原因（如 `CrashLoopBackOff`）。日志与追踪维度因容器未启动而不可用。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 注解引用了不存在的 NetworkAttachmentDefinition 'unavailable-network' → 
Multus CNI 无法检索到相应的网络委托配置 → 
Kubelet 因 Multus 插件报错无法创建 Pod 沙箱 → 
Pod 状态卡在 ContainerCreating (Pending)
```

### 根因结论

已确认根因为 **Multus CNI 配置错误**。Pod `workload-5dbb5dcd6c-nhd7v` 配置了多网卡功能，并引用了名为 `unavailable-network` 的 `NetworkAttachmentDefinition`，但该资源在 `aiops-case-05` 命名空间中不存在（见证据 #1）。这导致 Multus 插件初始化失败，阻碍了容器网络接口的挂载，使得 Pod 无法进入 Running 状态（见证据 #2）。

---

## 📊 性能统计

```text
├─ 总耗时: 9.7m
├─ 问题定位: 28.4s
├─ 并发证据采集: 548.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 548.5s (Evidence 540.0s, RCA 8.4s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-imagepull-failed, pod-sandbox-create-failed
