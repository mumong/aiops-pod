## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-nhd7v stuck in ContainerCreating state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason` = `ContainerCreating` (事实 ID: fact-0fe204f37107) | 确认 Pod 处于启动卡滞状态 |
| 2 | K8s Event | kubernetes | `Warning NoNetworkFound`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (事实 ID: fact-00bf752bd898) | 持续报告 Multus 插件找不到指定网络定义，频率高达 46 次 |
| 3 | K8s Event | kubernetes | `Warning FailedCreatePodSandBox`: `rpc error: code = Unknown desc = failed to setup network... plugin type="multus"... cannot find a network-attachment-definition (unavailable-network) not found` (事实 ID: fact-6acee151f9d8) | 揭示具体失败机制：Multus 插件在配置 pod 沙箱时，因引用了不存在的网络资源导致 RPC 报错并终止 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"}` = 1 (事实 ID: fact-06b372b50f66) | 数值确认容器持续处于等待状态，无法进入运行期 |

**证据关联说明：**
Kubernetes 状态数据 (事实 1) 与 Metric 指标 (事实 4) 一致表明 Pod 处于 `ContainerCreating` 阶段。事件数据 (事实 2 和 3) 提供了直接的因果链：`FailedCreatePodSandBox` 错误明确指出了失败原因为 Multus CNI 插件未能解析 Pod 定义中引用的 `unavailable-network` 网络附加定义。

## 🎯 根因分析 · g1

### 因果链

```text
Namespace 'aiops-case-05' 中缺失 'unavailable-network' NetworkAttachmentDefinition (事实 2) → Multus 插件无法解析 Pod 注解中的网络引用 (事实 3) → Kubelet 创建 Pod 沙箱网络配置时发生 RPC 错误 (事实 3) → Pod 卡在 ContainerCreating 状态 (事实 1, 4)
```

### 根因结论

**已确认根因：** 多租户 CNI (Multus) 插件因无法在 `aiops-case-05` 命名空间中找到名为 `unavailable-network` 的 `NetworkAttachmentDefinition` 资源，导致 Pod 网络插件配置失败。

这一缺失使得 Multus 在尝试为 Pod 附加网络时抛出 `NoNetworkFound` 警告，并进而触发 `FailedCreatePodSandBox` 错误，导致 Kubelet 无法完成容器的网络初始化，Pod 因此一直卡在 `ContainerCreating` 状态。

**缺失事实：** 无法确认 `unavailable-network` 资源是未被创建（配置遗漏）还是被意外删除。

---

## 📊 性能统计

```text
├─ 总耗时: 58.2s
├─ 问题定位: 19.3s
├─ 并发证据采集: 28.6s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 28.6s (Evidence 19.9s, RCA 8.5s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed, pod-sandbox-create-failed
