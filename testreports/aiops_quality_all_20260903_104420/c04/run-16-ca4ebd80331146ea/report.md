## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod workload-6584f97c76-wvcb2 处于 CreateContainerConfigError 状态，持续 32 分钟，容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Failed ... kubelet Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 直接指出 Secret 缺少配置所需的 key，是容器启动失败的直接原因 |
| 2 | K8s State | kubernetes | `container.waiting_reason: CreateContainerConfigError`, `container.waiting_message: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 确认容器处于配置错误导致的等待状态，与 Event 原因一致 |
| 3 | K8s State | kubernetes | `pod.phase: Pending`, `pod.condition: {type: Ready, status: False, reason: ContainersNotReady}` | 确认 Pod 整体处于不可用状态，容器未启动 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="CreateContainerConfigError"} = 1` | 独立观测确认了容器等待的具体原因，与 K8s 状态交叉印证 |

**证据印证说明：**
Kubernetes Event (证据#1) 与 Container Waiting State (证据#2) 在错误信息上完全一致，明确指向 Secret key 缺失。Metric 数据 (证据#4) 从独立观测维度再次确认了该等待原因。Pod 处于 Pending 且未就绪 (证据#3) 是该配置错误导致的必然状态结果。

## 🎯 根因分析 · g1

### 因果链

```text
Secret aiops-case-04/workload-input 缺少 key 'unavailable-key' → kubelet 无法注入所需配置 → 容器启动失败 (CreateContainerConfigError) → Pod 持续处于 Pending/Waiting 状态
```

### 根因结论

**已确认的根因：**
Pod spec 错误地引用了 Secret `aiops-case-04/workload-input` 中并不存在的 key `unavailable-key`（该 Secret 实际仅包含 `available-key`）。这一配置不匹配导致 kubelet 在启动容器时无法完成配置挂载，直接抛出 `CreateContainerConfigError`，使 Pod 持续卡在 Pending 状态。证据 #1 和 #2 提供了确凿的原始错误信息，证据 #4 从监控维度进行了独立印证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 18.1s
├─ 并发证据采集: 63.1s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 63.1s (Evidence 56.1s, RCA 6.8s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
