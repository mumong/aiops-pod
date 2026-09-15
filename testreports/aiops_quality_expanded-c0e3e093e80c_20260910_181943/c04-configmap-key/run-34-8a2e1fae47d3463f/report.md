## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 的容器配置引用了 ConfigMap `aiops-case-v11/workload-input` 中的 key `unavailable-key`，但该 ConfigMap 实际仅包含 `available-key`，导致 kubelet 无法注入配置从而处于 CreateContainerConfigError 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_message`: "couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input" (fact-407f4f1fbca2) | 直接指出配置文件注入失败的具体键名缺失事实 |
| 2 | K8s State | Kubernetes | `container.waiting_reason`: "CreateContainerConfigError" (fact-fa0853112d1c) | 确认容器因配置错误停留在等待状态 |
| 3 | K8s State | Kubernetes | `pod.phase`: "Pending" (fact-e95b094493e6) | 确认 Pod 整体处于未启动状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1, labels: {reason: "CreateContainerConfigError", container: "app"} (fact-2a022c19672d) | 通过监控指标独立确认了当前等待原因的数值状态 |

**证据说明：**
Kubernetes 状态中具体的 `waiting_message`（证据 1）精确指出了 ConfigMap 键名缺失的原因，与 K8s State 中的错误类型（证据 2）及 Metric 中的等待原因计数（证据 4）相互印证，共同指向配置加载失败，导致 Pod 处于 Pending 状态（证据 3）。由于容器未能启动，Log/Tracing 维度均无可用数据，现有 K8s 与 Metric 数据已完整闭合故障现象与直接原因。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'aiops-case-v11/workload-input' 缺少 key 'unavailable-key' → kubelet 注入配置失败 → 容器启动卡滞 (CreateContainerConfigError) → Pod 状态 Pending 且 app 容器不可用
```

### 根因结论

已确认根因：Pod `aiops-case-v11/workload` 的容器配置引用了 ConfigMap `aiops-case-v11/workload-input` 中不存在的 `unavailable-key`。
该事实由 K8s 状态信息（证据 1、2）直接支持，Metric 数据（证据 4）提供了独立的同步验证。Pod 处于 `Pending` 状态（证据 3）是该配置错误导致的直接表现。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 14.8s
├─ 并发证据采集: 45.3s
│  └─ g1 aiops-case-v11/workload: 45.3s (Evidence 38.8s, RCA 6.4s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
