## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-kbwsx 配置了 Multus CNI 引用名为 'unavailable-network' 的网络注解，但该命名空间下不存在对应的 NetworkAttachmentDefinition 资源，导致 Multus 插件无法完成沙箱网络初始化（FailedCreatePodSandBox），进而使 Pod 长期卡在 ContainerCreating (Pending) 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning NoNetworkFound multus cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (fact_id: fact-03eda8330966) | 证实 Multus 插件在多次尝试后均未找到预期的网络配置资源 |
| 2 | K8s Event | Kubernetes | `Warning FailedCreatePodSandBox kubelet Failed to create pod sandbox: ... plugin type="multus" ... getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (fact_id: fact-27ed053a8477) | 直接导致 Pod 沙箱创建失败的具体错误机制 |
| 3 | K8s State | Kubernetes | `ContainerCreating` (fact_id: fact-b772cb924684) | 确认 Pod 因上述网络问题被 Kubernetes 调度器/运行时卡在启动前状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1, label `reason="ContainerCreating"` (fact_id: fact-f78aa2f863c6) | 独立指标确认了容器状态的等待原因与事件状态一致 |

证据相互印证：Kubernetes 事件明确指出了底层原因是 `unavailable-network` 对应的 `NetworkAttachmentDefinition` 资源缺失（Fact #1），这一配置错误直接导致了 CNI 插件初始化失败和沙箱创建报错（Fact #2），最终表现为 Pod 长期处于 `ContainerCreating` 状态（Fact #3），并由监控指标（Fact #4）客观佐证了这一状态。

## 🎯 根因分析 · g1

### 因果链

```text
Namespace 缺少 NetworkAttachmentDefinition 资源 → Multus CNI 插件查找失败 → Pod 沙箱创建失败 → Pod 卡在 ContainerCreating (Pending) 状态
```

### 根因结论

已确认的根因是 Pod `aiops-case-05/workload-5dbb5dcd6c-kbwsx` 引用了名为 `unavailable-network` 的网络注解，但其所在的 `aiops-case-05` 命名空间内不存在对应的 `NetworkAttachmentDefinition` 资源。

这一事实由 K8s Event 事实 `fact-03eda8330966` 和 `fact-27ed053a8477` 明确证实：Multus 插件在初始化网络时因找不到指定资源而报错，直接阻断了 Pod 的运行。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 26.6s
├─ 并发证据采集: 36.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 36.5s (Evidence 30.4s, RCA 6.0s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed, pod-sandbox-create-failed
