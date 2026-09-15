## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-04/workload-6584f97c76-h4lt9` 状态为 `Pending`，且 `pod.phase` 确认处于等待态 | 确认异常实体的最终调度停滞状态 |
| 2 | K8s Event | Kubernetes | `Warning Failed`: "Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input" | 直接证明 kubelet 因配置项缺失而中止容器创建 |
| 3 | K8s State | Kubernetes | `container.waiting_reason`: `CreateContainerConfigError` | 对应异常现象，定位至容器配置校验失败阶段 |
| 4 | K8s State | Kubernetes | `container.waiting_message`: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input" | 精确指明缺失的配置资源及键名 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` | 独立验证该 Pod 的容器处于配置错误等待状态 |

证据说明：Kubernetes 的 Event 记录和状态字段（#2, #3, #4）直接给出了缺失键的明确报错原因，这与 Prometheus 指标中记录的特定等待原因（#5）相互印证。Pod 的 Pending 状态（#1）是该配置错误导致的直接系统表现，排除了调度或网络等其他维度的故障。

## 🎯 根因分析 · g1

### 因果链

```text
Secret aiops-case-04/workload-input 缺失 key unavailable-key → kubelet 在容器创建前校验配置失败 → Pod 停滞于 Pending 状态，容器报错 CreateContainerConfigError → 用户不可见应用日志或网络流量
```

### 根因结论

已确认的根因是 Pod 容器定义中引用的 Secret `aiops-case-04/workload-input` 中不存在必需的键 `unavailable-key`（证据 #2, #3, #4）。

该缺失导致 kubelet 在创建容器阶段无法完成配置注入，触发 `CreateContainerConfigError`。由于容器从未成功启动，系统未能产生应用日志或 Trace 数据（Logging/Tracing 维度为空），所有诊断证据均来源于 Kubernetes 状态与事件记录。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 35.8s
├─ 并发证据采集: 28.6s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 28.6s (Evidence 22.7s, RCA 5.9s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
