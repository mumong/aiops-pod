## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod spec 引用了 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key`，导致 kubelet 无法挂载配置。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (38m 内出现 12 次) | 确认导致容器启动失败的具体配置错误 |
| 2 | K8s State | Pod/app | Waiting 状态 `reason`: `CreateContainerConfigError`, `message`: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 验证当前 Pod 处于因配置缺失导致的容器化失败状态 |
| 3 | K8s State | Pod | `pod.phase`: `Pending`, `Ready`: `False` (Reason: `ContainersNotReady`) | 确认 Pod 停留在调度后无法启动的阶段 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` = `1` (app container) | 在监控层面确认识别出的错误类型与 K8s Event 一致 |

证据内容总结：Kubernetes 事件明确指出了 Pod `app` 容器因找不到 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key` 而陷入 `CreateContainerConfigError` 状态。监控数据（Metric）从外部观测验证了该容器因同一错误原因处于等待状态。Pod 的 `Pending` 和 `NotReady` 状态是该机制下的正常系统响应。由于容器始终未成功启动，日志（Logging）和追踪（Tracing）维度未产生应用数据。

## 🎯 根因分析 · g1

### 因果链

```text
Secret `aiops-case-04/workload-input` 中缺少 key `unavailable-key` → Pod spec 引用该 key 导致 kubelet 无法完成挂载与初始化 → 容器处于 CreateContainerConfigError 状态 → Pod 停留在 Pending 状态且未被调度进入 Running
```

### 根因结论

已确认的根因为：Pod `aiops-case-04/workload-6584f97c76-7ds5p` 的容器配置（spec）引用了 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key`，导致 kubelet 在初始化阶段因配置缺失而抛出 `CreateContainerConfigError` 异常，从而阻止了容器的启动 [证据 #1, #2]。

---

## 📊 性能统计

```text
├─ 总耗时: 59.3s
├─ 问题定位: 17.8s
├─ 并发证据采集: 33.3s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 33.3s (Evidence 26.3s, RCA 6.8s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
