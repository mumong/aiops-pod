## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 持续处于 CreateContainerConfigError 状态，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 根因定位：明确指出了 ConfigMap 挂载阶段因缺少特定 Key 导致的错误。 |
| 2 | K8s State | `pod.status` | `Pending` | 症状确认：Pod 由于配置加载失败无法进入 Running 状态。 |
| 3 | K8s Config | `container.resource_request.memory` | `app` 容器分配 `8Mi` | 上下文信息：提供了 Pod 的资源请求上下文。 |
| 4 | K8s Config | `container.resource_limit.memory` | `app` 容器限制 `32Mi` | 上下文信息：提供了 Pod 的资源限制上下文。 |
| 5 | Metric | `kube_pod_container_status_waiting_reason` | `CreateContainerConfigError` (Label: `container=app`) | 辅助确认：独立于 Event 的数据源也确认了容器处于因配置错误而等待的状态。 |

**证据总结**
Kubernetes Event（#1）提供了直接的失败原因，Metric 数据（#5）独立确认了等待原因为 `CreateContainerConfigError`。结合 Pod 状态（#2），事实闭环表明问题完全发生在 Pod 初始化阶段。由于容器未能启动，Logging 和 Tracing 维度无应用数据，符合预期。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了不存在的 ConfigMap Key -> kubelet 挂载配置失败 -> 容器启动被阻止 -> Pod 处于 CreateContainerConfigError 状态
```

### 根因结论

已确认根因为 **Pod 的容器配置引用了 ConfigMap 'workload-input' 中不存在的键 'unavailable-key'**（证据 #1, #5）。
该引用错误导致 kubelet 在挂载配置阶段失败，阻止了容器启动，从而引发了 Pod 持续处于 `CreateContainerConfigError` 的状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 16.3s
├─ 并发证据采集: 48.5s
│  └─ g1 aiops-case-v11/workload: 48.5s (Evidence 42.8s, RCA 5.5s)
└─ 汇总总结: 6.9s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
