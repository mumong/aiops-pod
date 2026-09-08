## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod 的容器配置引用了 Secret `workload-input` 中的 key `unavailable-key`，但该 Secret 实际仅包含 `available-key`，导致 Kubelet 在创建容器时因找不到必要配置而拒绝启动，Pod 持续处于 Pending/CreateContainerConfigError 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `waiting_reason: "CreateContainerConfigError"` | 明确容器状态异常为配置错误 |
| 2 | K8s Event | Kubernetes | `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 指出导致容器创建失败的具体缺失配置键 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (reason=`CreateContainerConfigError`) | 确认 Pod 处于配置等待状态的客观指标 |
| 4 | Metric | Prometheus | `kube_pod_status_phase=1` (phase=`Pending`), `restart_count=0` | 证明 Pod 停留在初始阶段，未发生过重启尝试 |

证据 1、2、3 相互印证，共同指向同一根因：Secret 引用缺失导致 Kubelet 在拉取容器前即失败。Metric 证据确认了该异常在监控视角下的持续状态，且 Restart Count 为 0 支持了“因配置问题直接阻断创建而非运行后崩溃”的推断。Logging/Tracing 维度因工具调用被拒绝（Forbidden）且无相关事实，不作为诊断依据。

## 🎯 根因分析 · g1

### 因果链

```text
Secret `workload-input` 缺失配置键 `unavailable-key` → Kubelet 拉取配置失败，触发 CreateContainerConfigError → 容器启动被阻断 → Pod 持续处于 Pending/CreateContainerConfigError 状态
```

### 根因结论

已确认根因为 **容器配置缺失**（Ref: #2）。
Pod 的 `app` 容器尝试引用 Secret `aiops-case-04/workload-input` 中的键 `unavailable-key`，但 Kubelet 无法找到该键（#2），导致 `CreateContainerConfigError`（#1）。该配置级失败阻止了容器的初始化，导致 Pod 长期停滞在 `Pending` 状态且未发生任何重启（#4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 26.8s
├─ 并发证据采集: 53.0s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 53.0s (Evidence 45.9s, RCA 7.0s)
└─ 汇总总结: 7.0s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
