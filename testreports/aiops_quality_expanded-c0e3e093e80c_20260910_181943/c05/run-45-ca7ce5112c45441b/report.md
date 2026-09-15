## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-bntfh is stuck in ContainerCreating state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Container "app" waiting_reason: `ContainerCreating` | 确认 Pod 处于启动前的阻塞状态，未进入运行阶段。 |
| 2 | K8s Event | kubernetes | `NoNetworkFound`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (持续 57 分钟，46 次) | 直接证明 Multus CNI 插件在指定命名空间内找不到所需的网络附属定义资源。 |
| 3 | K8s Event | kubernetes | `FailedCreatePodSandBox`: `failed to setup network for sandbox ... plugin type="multus" ... getKubernetesDelegate: cannot find a network-attachment-definition ... "unavailable-network" not found` (448 次) | 证实 kubelet 在尝试创建 Pod 沙箱（网络配置阶段）时失败，是容器卡在 ContainerCreating 的直接系统原因。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"}` 值为 `1` | 监控数据与 K8s 事件状态一致，确保持续处于该等待原因中。 |
| 5 | Logging | elasticsearch | 状态: `not_applicable`，限制: `容器未启动，物理上不会产生应用日志或业务 Trace` | 排除应用层或启动前日志的干扰，确认故障完全发生在容器启动前阶段。 |
| 6 | Tracing | deepflow/tempo | 状态: `not_applicable`，限制: `pod_ip is empty; Pod-scoped DeepFlow flow lookup cannot be executed` | 因未分配 IP 且容器未运行，网络流量与业务 Trace 不可采集，符合预期。 |

**证据关联说明：**
Kubernetes 状态（#1）与事件日志（#2, #3）高度一致，明确指出了故障点位于 CNI 网络插件的多重（Multus）委托加载阶段。由于 Pod 停留在创建前阶段，Metric 仅确认了该状态的持续性（#4），而 Logging（#5）和 Tracing（#6）因物理条件缺失无法提供额外信息，这排除了容器内部应用错误导致启动失败的可能。

## 🎯 根因分析 · g1

### 因果链

```text
Missing NetworkAttachmentDefinition CRD 'unavailable-network' → Multus CNI 无法解析网络委托配置 → Pod 沙箱创建失败 → 容器卡在 ContainerCreating 状态
```

### 根因结论

**已确认的根因**：Pod `aiops-case-05/workload-5dbb5dcd6c-bntfh` 无法启动是因为其网络配置依赖的 CNI 插件（Multus）未能找到名为 `unavailable-network` 的 `NetworkAttachmentDefinition` 资源。

证据（#2, #3）显示，Kubelet 在创建沙箱时连续报错 `getKubernetesDelegate: cannot find a network-attachment-definition`，且 Multus 插件在 `aiops-case-05` 命名空间中反复报 `NoNetworkFound` 错误。这是容器状态长期停滞在 `ContainerCreating` 的直接技术原因。目前确认为配置引用缺失或配置未正确部署导致的启动阻塞。

---

## 📊 性能统计

```text
├─ 总耗时: 6.9m
├─ 问题定位: 38.9s
├─ 并发证据采集: 365.2s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 365.2s (Evidence 358.0s, RCA 7.0s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-imagepull-failed, pod-volume-mount-failed
