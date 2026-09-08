## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod 注解指定的 NetworkAttachmentDefinition 'unavailable-network' 在命名空间 'aiops-case-05' 中不存在，导致 Multus CNI 无法配置网络，进而引发沙箱创建失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet (multus) | `Warning  NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` [fact-002393b2f66f, fact-04cd9c213f53] | 证明 Multus CNI 插件在多次重试中均失败，原因是找不到指定的网络定义资源。 |
| 2 | K8s Event | kubelet | `Warning  FailedCreatePodSandBox ... plugin type="multus" ... failed (add): Multus: ... GetNetworkDelegates: failed getting the delegate: ... "unavailable-network" not found` [fact-070a3ece4bc9] | 提供沙箱创建失败的直接原因，确认网络插件配置错误导致了容器运行时无法启动。 |
| 3 | K8s State | kubernetes | `container: "app", reason: "ContainerCreating"` [fact-118b44afdf4c] | 显示应用容器处于等待网络就绪的状态，印证了 CNI 插件配置失败导致的工作负载挂起。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (label: `reason="ContainerCreating"`, value: `1`) [fact-42de42403db3] | 确认该 Pod 实例目前仍持续处于因等待网络配置而挂起的状态。 |

**证据关联：**
K8s Event [fact-002393b2f66f] 详细列出了 "NoNetworkFound" 的具体报错，与 Event [fact-070a3ece4bc9] 中 kubelet 报告的沙箱创建失败直接互为因果。K8s State [fact-118b44afdf4c] 和 Metric [fact-42de42403db3] 从状态和指标层面确认了该 Pod 因上述配置错误而处于持续的 `ContainerCreating` 等待期。Logging/Tracing 因 Pod 未启动而自然不适用。

## 🎯 根因分析 · g1

### 因果链

```text
命名空间缺失网络定义资源 → Multus CNI 插件获取网络委托失败 → Pod 沙箱创建失败(rpc error) → 应用容器持续处于 ContainerCreating 状态
```

### 根因结论

已确认的根因是：Pod 规范中引用的 NetworkAttachmentDefinition `unavailable-network` 在命名空间 `aiops-case-05` 中不存在。

Multus CNI 插件在配置网络时找不到对应的定义资源（证据 `fact-002393b2f66f`），导致网络设置失败并向上抛出 `GetNetworkDelegates` 错误。此错误直接导致 kubelet 无法为 Pod `workload-5dbb5dcd6c-kbwsx` 创建沙箱（证据 `fact-070a3ece4bc9`），从而使容器卡在 `ContainerCreating` 状态等待网络就绪（证据 `fact-118b44afdf4c`, `fact-42de42403db3`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 16.9s
├─ 并发证据采集: 42.0s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 42.0s (Evidence 33.4s, RCA 8.4s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-imagepull-failed, pod-config-error, pod-volume-mount-failed, pod-sandbox-create-failed
