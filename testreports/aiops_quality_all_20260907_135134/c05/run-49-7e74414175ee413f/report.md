## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx 处于 ContainerCreating/Pending 状态，沙箱创建失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | fact-88c3a2ad9304: container="app" 处于 ContainerCreating 状态 | 确认 Pod 处于等待网络初始化的阻塞态 |
| 2 | K8s Event | multus | fact-03de7a5d5163: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (持续 60 分钟) | 直接证据：Multus CNI 因缺少特定网络定义报错 |
| 3 | K8s Event | kubelet | fact-32211f022ce4: `Failed to create pod sandbox: rpc error... plugin type="multus" ... failed (add)` (x426 over 97m) | 确认 kubelet 尝试创建沙箱时因网络插件失败而受阻 |
| 4 | Metric | prometheus | fact-58ddd8b8ae78: `kube_pod_container_status_waiting_reason` 值为 1 (container="app", reason="ContainerCreating") | 监控侧证实 Pod 持续处于因网络问题导致的等待态 |

**证据印证说明**：
Kubernetes 状态与事件（证据 1-2）直接指向配置缺失：Pod 引用的 `unavailable-network` 资源不存在。Kubelet 事件（证据 3）证实了该缺失资源导致沙箱创建失败，Prometheus 指标（证据 4）进一步确认该状态非瞬时异常，而是长期持续。Metric 仅有一个样本，无法评估趋势，但结合长达 97 分钟的 Event 聚合记录，足以证明故障未自愈。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了不存在的 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件加载 delegate 失败 → Kubelet 无法创建 Pod Sandbox → Pod 处于 ContainerCreating/Pending 状态，用户服务不可用
```

### 根因结论

已确认根因：Pod `aiops-case-05/workload-5dbb5dcd6c-kbwsx` 的 Spec 中引用了一个在当前命名空间内不存在的 NetworkAttachmentDefinition 资源（名称：`unavailable-network`）。

这一缺失导致 Multus CNI 插件在尝试为 Pod 初始化网络时无法找到对应的 delegate 配置，从而报错退出。该网络初始化失败直接阻断了 Kubelet 创建 Pod Sandbox 的流程，使得 Pod 中的 `app` 容器无法启动，始终停留在 `ContainerCreating` 状态（证据 1、2、3、4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 55.6s
├─ 并发证据采集: 49.1s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 49.1s (Evidence 39.7s, RCA 9.2s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-sandbox-create-failed
