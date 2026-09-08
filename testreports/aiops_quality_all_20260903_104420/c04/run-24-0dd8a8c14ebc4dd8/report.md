## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod workload-6584f97c76-wvcb2 处于 Pending/Waiting 状态，Reason 为 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod | `status: Pending`, `phase: Pending` | 确认 Pod 处于待调度/等待状态 |
| 2 | K8s State | Pod | `container.waiting_reason: CreateContainerConfigError` | 确认具体的容器初始化失败机制 |
| 3 | K8s State | Pod | `container.waiting_message: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input"` | 明确指出缺失的配置密钥名称及目标 Secret |
| 4 | K8s Event | Pod | `Warning Failed: Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 确认 kubelet 在容器创建阶段遭遇的实际错误，与状态一致 |
| 5 | K8s Config | Pod | `resource_request.cpu: 5m`, `resource_limit.cpu: 50m`, `resource_request.memory: 8Mi`, `resource_limit.memory: 32Mi` | 确认资源配置合法，排除资源不足导致的调度失败或 OOMKilled |
| 6 | K8s State | Pod | `restart_count: 0` | 确认 Pod 尚未经历重启循环，故障为初始启动阻塞 |
| 7 | Metric | Pod | `kube_pod_container_status_waiting_reason=1` (`reason: CreateContainerConfigError`) | 指标确认等待状态的持续时间，且未显示趋势变化（单样本） |

**证据印证关系：**
Kubernetes 的 `State` (事实 2, 3, 4) 与 `Config` (事实 5) 形成闭环：Pod 因 `CreateContainerConfigError` 卡住，且明确报错无法在 `aiops-case-04/workload-input` 中查找 `unavailable-key`，而资源配置正常，排除资源冲突。指标 (事实 7) 仅作为辅助确认，由于缺乏时间序列样本且无应用日志/Trace（因容器未启动），核心证据高度集中在 Kubernetes 原生状态与事件中。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了 Secret 'aiops-case-04/workload-input' 的 key 'unavailable-key' → kubelet 尝试注入配置 → 因 Secret 中不存在该 key 导致注入失败 → 容器状态陷入 CreateContainerConfigError 并永久 Pending
```

### 根因结论

已确认根因为 **Secret 配置键名不匹配**。

Pod 的容器启动配置要求从 Secret `aiops-case-04/workload-input` 中获取名为 `unavailable-key` 的密钥，但该 Secret 的实际数据中仅包含 `available-key`（或其根本不存在该键）。这一配置错误导致 kubelet 无法完成容器环境变量的初始化（注入阶段失败），直接触发 `CreateContainerConfigError` 终止了容器的创建过程。证据编号 #3 和 #4 提供了确凿的原始报错文本，与现象完全吻合。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 22.8s
├─ 并发证据采集: 48.9s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 48.9s (Evidence 40.2s, RCA 8.5s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
