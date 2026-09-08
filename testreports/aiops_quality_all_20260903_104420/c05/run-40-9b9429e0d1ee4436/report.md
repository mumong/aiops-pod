## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v in aiops-case-05 stuck in ContainerCreating (Pending) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: `ContainerCreating` (container: app) | 确认 Pod 处于等待状态，容器未启动 |
| 2 | K8s Event | kubernetes | `Warning NoNetworkFound`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` (46 条，最近 2s) | 持续报错表明指定的网络定义缺失，导致网络插件失败 |
| 3 | K8s Event | kubernetes | `Warning FailedCreatePodSandBox`: `rpc error: code = Unknown desc = failed to setup network for sandbox ... plugin type="multus" name="multus-cni-network" failed (add)` (512 over 116m) | 确认根本机制是 Multus 插件因找不到 NAD 导致 Pod 沙箱创建失败 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (container: app, reason: ContainerCreating) = 1 (`sample_count`: 1, `trend_evaluable`: false) | 量化验证容器当前停留在等待阶段 |

**证据说明：**
Kubernetes 事件 (`fact-12c012a4dbaa`, `fact-01d7eb3fbc8c`) 与容器状态 (`fact-17a945ccf8cc`) 互相印证。Pod 因引用的 Multus `NetworkAttachmentDefinition` ("unavailable-network") 在 `aiops-case-05` 命名空间中不存在，无法配置网络，直接导致 `FailedCreatePodSandBox`，进而使容器长期处于 `ContainerCreating` 状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 引用缺失的 NetworkAttachmentDefinition 'unavailable-network' (g1:fact-01d7eb3fbc8c) → Multus CNI 插件查找失败 (g1:fact-12c012a4dbaa) → 创建 Pod 沙箱失败 (g1:fact-12c012a4dbaa) → Pod 卡在 ContainerCreating 状态 (g1:fact-17a945ccf8cc)
```

### 根因结论

已确认的根因是 Pod 声明了一个不存在的 Multus `NetworkAttachmentDefinition` (`unavailable-network`)。

- **原因**：Pod 在 `aiops-case-05` 命名空间中引用了名为 `unavailable-network` 的 `NetworkAttachmentDefinition` (NAD)（证据见 `fact-01d7eb3fbc8c`, `fact-12c012a4dbaa`）。
- **机制**：Multus CNI 插件尝试加载该网络配置，但 API 返回 "not found" 错误，导致无法为 Pod 配置底层网络接口。
- **现象**：由于网络配置失败，kubelet 无法创建 Pod 沙箱 (`FailedCreatePodSandBox`)，导致容器持续处于 `ContainerCreating` 状态（证据见 `fact-17a945ccf8cc`, `fact-74f2aad4be71`）。

---

## 📊 性能统计

```text
├─ 总耗时: 9.4m
├─ 问题定位: 14.7s
├─ 并发证据采集: 536.6s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 536.6s (Evidence 529.3s, RCA 7.1s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed, pod-sandbox-create-failed, pod-pending-unschedulable
