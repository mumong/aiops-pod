## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod workload (aiops-case-v11) 处于 CreateContainerConfigError 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Failed ... 32m (x12 over 34m) kubelet ... Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 核心因果：提供精确缺失的 ConfigMap 键名及来源实体，直接指向配置错误。 |
| 2 | K8s State | Kubernetes | `container.waiting_reason: CreateContainerConfigError`, `container.waiting_message: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` | 核心因果：复述 Kubelet 判定失败的确切原因，与 Event 一致。 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (`container: app`, `reason: CreateContainerConfigError`) = 1 | 独立指标印证：Prometheus 确认容器处于 `CreateContainerConfigError` 等待状态，排除瞬时异常。 |
| 4 | K8s State | Kubernetes | `pod.status: Pending`, `pod.phase: Pending`, `ContainersReady: False` | 异常状态确认：证实 Pod 处于初始化未完成阶段，且 `ContainersNotReady`。 |
| 5 | K8s Config | Kubernetes | `resource_request.memory: 8Mi`, `resource_limit.cpu: 50m` | 资源上下文：排除因资源请求或限制导致的调度或启动失败（资源并非导致 ConfigError 的原因）。 |
| 6 | Logging/Tracing | ES/Deepflow/Tempo | `status: not_applicable`, `limitations: 容器未启动，物理上不会产生应用日志或业务 Trace` | 排除干扰：证实因容器未能启动，日志和追踪维度的缺失属于正常物理现象，不构成证据断层。 |

**证据综合说明：**
证据 1 (Event) 与证据 2 (State Message) 提供了完全一致且具体的失败信息：ConfigMap `aiops-case-v11/workload-input` 缺少键 `unavailable-key`。证据 3 (Metric) 从监控维度确认了该状态已稳定存在。证据 6 (Logs/Tracing) 解释了为何未观测到更多详细日志：由于 Kubelet 在启动容器前置检查阶段失败，应用容器本身未运行，因此无业务日志或 Trace 可供排查。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'aiops-case-v11/workload-input' 缺失键 'unavailable-key' → Kubelet 挂载配置时触发 'couldn't find key' 错误 → 容器启动前置检查失败，进入 CreateContainerConfigError → Pod 停留在 Pending/ContainersNotReady 状态
```

### 根因结论

已确认的根因是 Pod 定义中引用了 ConfigMap `aiops-case-v11/workload-input` 中的键 `unavailable-key`，但该键在 ConfigMap 中不存在。

该配置错误导致 Kubelet 在初始化容器时无法获取所需的配置值，从而抛出 `CreateContainerConfigError` 并使 Pod 处于等待状态。

**支持证据：**
- 证据 1：Kubernetes Event 明确记录了 `couldn't find key unavailable-key` 的错误信息。
- 证据 2：容器等待消息精确复述了该错误。
- 证据 3：Metric 数据验证了容器长期处于 `CreateContainerConfigError` 状态。

**缺失事实：**
目前证据仅确认了技术层面的键缺失，未包含业务逻辑层面的决定性事实：即 `unavailable-key` 具体期望的业务值是什么，以及正确的修复方向是补充该键还是修改 Pod 定义以使用现有的 ConfigMap 键。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 17.4s
├─ 并发证据采集: 81.0s
│  └─ g1 aiops-case-v11/workload: 81.0s (Evidence 72.3s, RCA 8.6s)
└─ 汇总总结: 12.1s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
