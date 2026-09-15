## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-h4lt9 引用了 Secret aiops-case-04/workload-input 中不存在的 key 'unavailable-key'，该 Secret 实际仅包含 'available-key'，导致 kubelet 无法挂载配置并报错 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接证实 Kubelet 尝试挂载配置失败的具体原因是密钥不存在 |
| 2 | K8s State | Container | `waiting_reason: CreateContainerConfigError` (Container: `app`) | 确认容器因配置问题处于等待状态，且原因类型匹配 |
| 3 | K8s State | Pod | `phase: Pending`, `condition: ContainersNotReady` | 确认 Pod 处于未就绪阶段，符合配置错误的典型状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason[1]` (reason: `CreateContainerConfigError`) | 独立于 K8s 状态的指标验证，确认集群监控侧也捕获到相同的错误原因 |

证据与 K8s 事实高度一致：Kubelet 事件（#1）给出了导致 `CreateContainerConfigError`（#2）的具体错误原因（Secret Key 缺失）。Metrics（#4）作为独立观测源，证实了该异常状态的持续存在。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用不存在的 Secret Key ('unavailable-key') → Kubelet 无法挂载配置 → 容器创建失败 (CreateContainerConfigError) → Pod 状态为 Pending / ContainersNotReady
```

### 根因结论

已确认的根因是：Pod `aiops-case-04/workload-6584f97c76-h4lt9` 的容器 `app` 引用了 Secret `aiops-case-04/workload-input` 中不存在的 key `'unavailable-key'`（该 Secret 实际仅包含 `'available-key'`）。

这一配置不匹配导致 Kubelet 在初始化容器时无法找到所需配置数据，从而抛出 `CreateContainerConfigError` 并拒绝启动容器。相关证据见表项 #1 (Kubelet 错误原文) 和 #2 (容器状态)。

---

## 📊 性能统计

```text
├─ 总耗时: 53.6s
├─ 问题定位: 18.9s
├─ 并发证据采集: 27.5s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 27.5s (Evidence 22.8s, RCA 4.6s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
