## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod 配置引用了 Secret 'aiops-case-04/workload-input' 中不存在的 key 'unavailable-key'，导致 kubelet 在启动容器 app 时无法注入环境变量或挂载卷，从而陷入 CreateContainerConfigError 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Failed ... Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 揭示容器启动的具体失败原因（Secret Key 缺失） |
| 2 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason=1` (reason: `CreateContainerConfigError`) | 验证并量化当前 Pod 处于配置错误状态的宏观表现 |

日志（Logging）与追踪（Tracing）维度因容器未成功启动而物理上无相关数据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用 Secret 'aiops-case-04/workload-input' 中不存在的 key 'unavailable-key' → kubelet 无法完成环境变量或挂载卷注入 → 容器启动失败 (CreateContainerConfigError) → Pod 处于 Pending 等待状态
```

### 根因结论

**已确认根因**：Pod 配置错误地引用了 Secret `aiops-case-04/workload-input` 中不存在的 `unavailable-key`。
Kubelet 在尝试启动容器 `app` 时发现该 key 不存在，导致无法注入环境变量或挂载卷，从而将 Pod 保持在 `CreateContainerConfigError` 状态。该结论由 Kubernetes 事件（#1）中 `kubelet` 的明确报错信息以及 Prometheus 指标中对应的 `CreateContainerConfigError` 状态（#2）共同证实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 19.3s
├─ 并发证据采集: 35.4s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 35.4s (Evidence 28.9s, RCA 6.5s)
└─ 汇总总结: 5.4s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
