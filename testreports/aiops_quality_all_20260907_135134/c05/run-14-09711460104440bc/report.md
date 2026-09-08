## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod 通过注解 `k8s.v1.cni.cncf.io/networks` 引用了名为 `unavailable-network` 的 NetworkAttachmentDefinition，但该资源在 namespace `aiops-case-05` 中不存在。Multus CNI 插件因找不到该网络定义而无法建立网络插件链，导致 kubelet 反复失败创建 Pod Sandbox，使 Pod 卡在 ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `waiting_reason: ContainerCreating` (fact-...d2a3) | 确认为 Pod 启动阻塞状态 |
| 2 | K8s Event | Multus | `NoNetworkFound`: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05) (fact-...0a6f) | 直接归因于 Multus CNI 插件未能找到注解中指定的网络资源 |
| 3 | K8s Event | Kubelet | `FailedCreatePodSandBox`: rpc error ... plugin type="multus" ... failed (add): Multus: ... cannot find a network-attachment-definition (unavailable-network) ... not found (fact-...1787) | 证实 Multus 插件链加载失败是导致容器运行时沙箱创建失败的具体原因 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (container: app, reason: ContainerCreating) = 1 (fact-...2709) | 监控指标从侧面印证 Pod 处于等待状态 |

**证据印证关系：**
K8s 事件表明 Multus 插件链因找不到 `unavailable-network` 而加载失败 (事实 #2, #3)，这直接解释了 Kubelet 无法创建 Pod 沙箱，从而导致了 K8s 状态 (事实 #1) 与监控指标 (事实 #4) 中显示的 `ContainerCreating` 阻塞现象。由于容器尚未启动，Logging/Tracing 维度不适用。

## 🎯 根因分析 · g1

### 因果链

```text
Namespace 'aiops-case-05' 中缺失 'unavailable-network' 网络定义 (事实 #2) → Multus CNI 插件链初始化失败 (事实 #3) → Kubelet 创建 Pod Sandbox 报错失败 (事实 #3) → Pod 状态持续卡在 ContainerCreating (事实 #1, #4)
```

### 根因结论

已确认根因：Pod 注解引用了不存在的 `NetworkAttachmentDefinition` (名称为 `unavailable-network`)，导致 Multus 插件链断裂，进而引发 Pod 启动阻塞。该结论由 Kubelet 和 Multus 的报错事件强支撑。
未知因素：未查明该 `NetworkAttachmentDefinition` 未创建的根本原因，也未确认 Pod 本是否应使用默认网络。

---

## 📊 性能统计

```text
├─ 总耗时: 6.6m
├─ 问题定位: 26.2s
├─ 并发证据采集: 363.7s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 363.7s (Evidence 354.4s, RCA 9.1s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed
