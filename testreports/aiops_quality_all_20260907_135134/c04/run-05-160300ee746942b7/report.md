## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-7ds5p 的容器定义中通过 env 引用了 Secret 'workload-input' 中的 key 'unavailable-key'，但该 Secret 实际数据中仅包含 'available-key'，导致 kubelet 无法注入环境变量并引发 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `Failed ... Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 明确指出了 kubelet 在尝试注入环境变量时找不到 Secret 中指定 key 的直接报错。 |
| 2 | K8s State | `kubernetes` | `container.waiting_reason: CreateContainerConfigError` | 容器当前处于等待状态，且原因明确为配置注入错误。 |
| 3 | K8s State | `kubernetes` | `container.waiting_message: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 进一步确认了容器无法启动的具体原因是缺失的 Secret Key。 |
| 4 | K8s State | `kubernetes` | `pod.phase: Pending`, `pod.condition.Ready: False`, `pod.condition.ContainersReady: False` | 确认 Pod 处于 Pending 阶段，且主容器 `app` 未就绪。 |
| 5 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason {reason="CreateContainerConfigError"} = 1` | 从监控指标确认了该 Pod 处于因配置错误导致的等待状态。 |

**证据说明**：Kubernetes 的事件日志（#1）、容器状态（#2, #3）与监控指标（#5）在“`CreateContainerConfigError`”和“`unavailable-key` 缺失”这两个核心事实上完全一致，构成了完整的故障证据链。日志与追踪数据未采集（`not_applicable`）因容器未启动属于预期行为，不影响当前证据的充分性。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'workload-input' 中缺失 'unavailable-key' → kubelet 无法注入环境变量 → 容器启动配置失败 → Pod 处于 Pending 状态，容器报 CreateContainerConfigError
```

### 根因结论

已确认的根因是 **Pod 定义中通过环境变量引用了不存在的 Secret Key**。具体而言，`aiops-case-04/workload-6584f97c76-7ds5p` 的容器配置试图从 `aiops-case-04/workload-input` 这个 Secret 中获取名为 `unavailable-key` 的数据，但该 Secret 实际并不包含此 Key。这一配置错误导致 kubelet 在初始化容器时失败，从而引发 `CreateContainerConfigError`，使 Pod 处于 Pending 状态。该结论由 K8s 事件日志、容器等待状态及监控指标直接支持。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.0s
├─ 并发证据采集: 41.5s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 41.4s (Evidence 35.3s, RCA 6.0s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
