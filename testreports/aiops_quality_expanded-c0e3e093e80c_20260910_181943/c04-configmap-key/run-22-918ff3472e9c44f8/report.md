## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 持续处于 Pending 状态且容器状态为 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Failed ... Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 直接揭示配置引用错误 |
| 2 | K8s State | kubernetes | `container.waiting_reason: CreateContainerConfigError` | 确认容器因配置问题处于等待状态 |
| 3 | K8s State | kubernetes | `pod.phase: Pending`, `containers with unready status: [app]` | 确认 Pod 未进入运行状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"} = 1` | 独立指标确认等待原因 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total = 0` | 确认容器从未启动过，排除了运行时崩溃 |
| 6 | K8s Config | kubernetes | `container.resource_request.memory: 8Mi`, `container.resource_limit.cpu: 50m` | 排除资源配额不足导致调度的可能性 |

**证据印证：**
Metric 维度（#4, #5）与 Kubernetes 维度（#1, #2）在“容器因配置错误等待且未重启”这一事实上完全一致。Event 中的具体错误原文直接锁定了缺失的 ConfigMap 键名。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了 ConfigMap 中不存在的键 'unavailable-key' → kubelet 挂载配置失败 → 容器启动触发 CreateContainerConfigError → Pod 保持 Pending 状态
```

### 根因结论

已确认的根因是 Pod 的 Spec 错误地引用了 `ConfigMap aiops-case-v11/workload-input` 中不存在的键 `'unavailable-key'`（证据 #1, #2, #4）。

该错误导致 kubelet 在初始化容器阶段无法找到所需的配置项，从而拒绝创建容器。由于容器始终未进入 Running 状态，因此也没有发生重启（证据 #5, #6）。

---

## 📊 性能统计

```text
├─ 总耗时: 58.9s
├─ 问题定位: 15.9s
├─ 并发证据采集: 35.7s
│  └─ g1 aiops-case-v11/workload: 35.7s (Evidence 27.3s, RCA 8.2s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
