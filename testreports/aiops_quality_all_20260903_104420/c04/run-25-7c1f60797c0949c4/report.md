## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 的容器配置引用了 Secret aiops-case-04/workload-input 中不存在的 key 'unavailable-key'（实际仅包含 'available-key'），导致 Kubelet 无法注入环境变量/卷，进而触发 CreateContainerConfigError 并持续处于 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Pod Status | `Pending` | 确认为 Pod 级阻塞，容器未启动，无法运行应用 |
| 2 | K8s State | K8s Container | `reason: CreateContainerConfigError`, `message: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input"` | 定位到配置错误，Kubelet 在挂载配置时因 Secret Key 缺失而失败 |
| 3 | K8s Event | K8s Event | `Warning Failed ... Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 提供 Kubelet 侧重复触发的明确失败上下文 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 持续为 `1`，`reason=CreateContainerConfigError` | 确认该配置错误为持续性阻塞，非瞬时故障 |
| 5 | K8s State | K8s Pod Condition | `ContainersReady: False` (`reason: ContainersNotReady`) | 验证了 Pod 就绪条件的根本原因 |

**证据互证说明：**
`K8s State` 中的 `CreateContainerConfigError` 状态与 `K8s Event` 中的失败日志完全一致，共同指向 Secret 中缺失特定 key。Metric 数据进一步证实了这一配置错误是导致容器持续处于等待状态的直接原因，未发生容器启动尝试，因此没有日志或链路证据。

## 🎯 根因分析 · g1

### 因果链

```text
Secret aiops-case-04/workload-input 缺少 Pod 配置引用的 key 'unavailable-key' → Kubelet 注入容器配置失败 (CreateContainerConfigError) → Pod 持续处于 Pending 状态 → 业务不可用
```

### 根因结论

已确认根因为 `Pod aiops-case-04/workload-6584f97c76-wvcb2` 的容器配置引用了 Secret `aiops-case-04/workload-input` 中不存在的 key `'unavailable-key'`。该配置不一致导致 Kubelet 无法完成配置挂载，进而持续抛出 `CreateContainerConfigError`。证据链闭环：`K8s State` (fact #2) 与 `K8s Event` (fact #3) 提供了确切的错误原文与原因，`Metric` (fact #4) 排除了容器启动重试或瞬时故障的可能性。缺失的日志与追踪数据系因容器未启动导致，不属于诊断阻碍。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 20.0s
├─ 并发证据采集: 81.5s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 81.5s (Evidence 74.0s, RCA 7.3s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
