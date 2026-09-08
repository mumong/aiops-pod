## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v 的 Multus CNI Annotation 引用了不存在的 NetworkAttachmentDefinition 'unavailable-network'，导致 Multus 无法创建 Pod Sandbox 并触发持续重试。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (kubelet) | `fact-a5f6a5a1a773`: `Warning FailedCreatePodSandBox ... Failed to create pod sandbox: ... plugin type="multus" name="multus-cni-network" failed (add) ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05) ... not found` | 确证 Pod 无法创建沙箱的直接错误机制及关联组件 |
| 2 | K8s Event | kubernetes (multus) | `fact-5e921a58a14b` (最近): `Warning NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05) ... not found` | 持续触发 `unavailable-network` 查找失败的源事件模式 |
| 3 | K8s State | kubernetes | `fact-13c83ca058c9`: `container "app"` 状态为 `ContainerCreating` (waiting) | 展示异常持续时间及容器停滞状态 |
| 4 | Metric | prometheus | `fact-8063ef93bf09`: `kube_pod_container_status_waiting_reason` 值为 `1`，标签 `reason="ContainerCreating"` | 独立印证容器持续处于等待状态 |

**证据说明：**
事件 `fact-a5f6a5a1a773` 与 `fact-5e921a58a14b` 互为表里，明确了 `multus` CNI 插件因找不到 `network-attachment-definitions` 资源而调用失败，进而阻止 `kubelet` 创建 Pod 沙箱。Metric `fact-8063ef93bf09` 确认该状态已持续存在。日志与追踪数据因容器未启动而不适用（符合预期）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 的 Multus CNI Annotation 引用了不存在的 NetworkAttachmentDefinition 'unavailable-network' → Multus 查找失败并报错 → kubelet 无法创建 Pod Sandbox → Pod 卡在 ContainerCreating 状态并持续重试
```

### 根因结论

**已确认的根因：**
Pod `workload-5dbb5dcd6c-nhd7v` 的 Multus CNI 配置错误地引用了名为 `unavailable-network` 的网络附件定义，但命名空间 `aiops-case-05` 中不存在该资源（证据 1, 2）。这一缺失导致 Multus 插件初始化网络时失败，直接引发 `FailedCreatePodSandBox` 错误，使 Pod 陷入持续重试并卡在 `ContainerCreating` 状态（证据 3, 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 29.2s
├─ 并发证据采集: 54.3s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 54.3s (Evidence 48.9s, RCA 5.3s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-imagepull-failed, pod-sandbox-create-failed
