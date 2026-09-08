## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-7ds5p 处于 CreateContainerConfigError 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Failed`: Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input (x12 over 9m19s) | 确证 kubelet 因找不到指定 Secret key 导致容器创建失败 |
| 2 | K8s State | Kubernetes | 状态: `Pending`; 重启次数: 0 | 证实 Pod 因配置错误被阻断启动，且未发生后续重启 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` 值为 1 | 从监控层独立证实 Pod 容器处于配置缺失的等待状态 |

**证据互证说明**：
K8s Event 提供了确切的错误原文，指明缺失的 key 为 `unavailable-key` 且所属 Secret 为 `aiops-case-04/workload-input`。Metric 的 `CreateContainerConfigError` 状态与 K8s Event 的失败原因一致，且 Pod 重启次数为 0，说明该配置校验失败发生在容器启动的最初阶段，未触发重试循环。

## 🎯 根因分析 · g1

### 因果链
```text
Pod spec 中引用的 Secret key 'unavailable-key' 不存在于 Secret 'aiops-case-04/workload-input' 中 → kubelet 在加载容器配置时校验失败 → 容器启动被阻断，状态设为 Pending/Waiting → Pod 持续无法运行，未产生应用日志
```

### 根因结论
已确认根因为 Pod spec 中引用的 Secret key `unavailable-key` 在 Secret `aiops-case-04/workload-input` 中不存在（证据 #1、#3）。这导致 kubelet 无法完成配置加载，从而阻止了容器的创建与启动。

存在未确认项：无法判定该 key 是被误删除还是存在拼写错误，以及该 key 的正确名称应为何（需通过比对 Secret 实际存储内容与 Pod spec 定义来确认）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 15.2s
├─ 并发证据采集: 42.4s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 42.4s (Evidence 33.9s, RCA 8.4s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
