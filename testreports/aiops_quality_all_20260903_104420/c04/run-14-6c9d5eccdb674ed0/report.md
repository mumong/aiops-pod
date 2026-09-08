## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod `aiops-case-04/workload-6584f97c76-wvcb2` 状态为 `Pending`，容器 `app` 处于 `Waiting` 状态，原因 `CreateContainerConfigError`。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-04/workload-6584f97c76-wvcb2` 状态 `Pending`，容器 `app` 原因 `CreateContainerConfigError` | 明确当前阻断状态与容器等待阶段 |
| 2 | K8s Config | Kubernetes | `container.waiting_message`: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input" | 直接定位缺失的 Secret 配置项名 |
| 3 | K8s Event | Kubernetes | "Warning Failed ... kubelet ... Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input" | 独立确认 kubelet 失败触发点与 Secret 缺失事实 |
| 4 | K8s State | Kubernetes | Pod Condition `Ready=False`, `ContainersReady=False`, Reason `ContainersNotReady` | 证实 Pod 未就绪状态由容器未就绪引发 |
| 5 | K8s Config | Kubernetes | `container.resource_request.memory=8Mi`, `container.resource_request.cpu=5m`, `limit_cpu=50m`, `limit_memory=32Mi` | 排除资源配额不足导致 Pending 的可能性 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 `1` (labels: `container=app`, `reason=CreateContainerConfigError`) | 辅助确认容器处于配置错误等待态 |

**证据说明：**
- **K8s State 1 & 6** 共同确认容器处于 `CreateContainerConfigError` 等待状态。
- **K8s Config 2 & 3** 独立且一致地揭示了根本原因：Pod 配置引用的 `unavailable-key` 在 Secret `aiops-case-04/workload-input` 中缺失。
- **K8s Config 5** 排除了资源请求过高导致的调度或启动失败。

## 🎯 根因分析 · g1

### 因果链

```text
Secret `workload-input` 缺少 Pod 配置引用的 key `unavailable-key` → 容器 `app` 初始化时无法解析 Secret 键值 → kubelet 触发 `CreateContainerConfigError` 失败事件 → Pod 持续停留在 Pending 状态未恢复
```

### 根因结论

已确认根因为 **Pod 配置错误引用了不存在的 Secret 键**。

Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的容器 `app` 在配置环境变量时，引用了 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key`。该 key 在 Secret 中并不存在（实际存在的是 `available-key`），且配置未设置 `optional=true`。这导致 kubelet 在尝试挂载配置时失败，直接抛出 `CreateContainerConfigError`，进而使 Pod 无法启动并一直处于 Pending 状态（证据编号：3, 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 18.8s
├─ 并发证据采集: 58.2s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 58.2s (Evidence 47.5s, RCA 10.5s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
