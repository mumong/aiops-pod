## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-h4lt9 的容器配置中引用了 Secret workload-input 中的 key unavailable-key，但该 Secret 实际仅包含 key available-key，导致 kubelet 无法获取配置并处于 CreateContainerConfigError 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Phase: Pending | 确认 Pod 处于等待启动状态，无法进入 Running。 |
| 2 | K8s State | kubernetes | Container `app` Waiting Reason: `CreateContainerConfigError` | 直接定位容器启动失败阶段在配置获取期。 |
| 3 | K8s State | kubernetes | Container `app` Waiting Message: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 提供导致容器配置失败的精确错误描述。 |
| 4 | K8s Event | kubernetes | `Failed` Event: `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 从 Kubelet 视角复现了获取 Secret 密钥失败的事件。 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError", container="app"} = 1` | 独立于 K8s API 的外部观测，印证了当前的异常状态。 |

**证据说明：**
Kubernetes 状态、事件与 Prometheus 指标三方数据（#2, #3, #4, #5）高度一致，均指向 `CreateContainerConfigError` 状态，并明确指出了错误源头是 Secret `workload-input` 中缺失 Key `unavailable-key`。因容器未启动，Log 和 Tracing 维度无法采集有效诊断数据。

## 🎯 根因分析 · g1

### 因果链
```text
Secret workload-input 缺失 Pod 期望的 key 'unavailable-key' → Kubelet 无法获取容器配置 → 容器启动失败 (CreateContainerConfigError) → Pod 处于 Pending 状态
```

### 根因结论
已确认的根因是 Pod 配置引用了不存在的 Secret Key。证据表明，Pod 容器配置中指定了从 Secret `workload-input` 获取名为 `unavailable-key` 的值，但该 Key 在目标 Secret 中实际不存在，导致 Kubelet 在拉起容器前因配置校验失败而终止启动流程（见证据 #3, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 20.9s
├─ 并发证据采集: 50.3s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 50.3s (Evidence 43.0s, RCA 7.1s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
