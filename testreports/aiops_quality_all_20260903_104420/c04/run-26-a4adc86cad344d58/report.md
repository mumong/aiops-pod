## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod workload-6584f97c76-wvcb2 的容器配置中引用了 Secret 'workload-input' 中不存在的 key 'unavailable-key'，导致 kubelet 无法完成容器配置创建，从而进入 CreateContainerConfigError 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Failed: Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (56分钟内发生12次) | 核心证据。kubelet 明确指出因缺失 Secret Key 导致配置失败。 |
| 2 | K8s State | Kubernetes | `container.waiting_reason: CreateContainerConfigError` | 确认当前状态为配置错误导致的等待，非运行时异常。 |
| 3 | K8s State | Kubernetes | `container.waiting_message: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 具体指出缺失键名及所在 Secret，为根因提供精确依据。 |
| 4 | K8s State | Kubernetes | `pod.condition: phase=Pending, ContainersReady=False, reason=ContainersNotReady` | 确认 Pod 处于调度成功但未就绪状态。 |
| 5 | K8s Config | Kubernetes | `container.resource_request.cpu: 5m, memory: 8Mi` (Context) | 排除资源不足导致的调度失败，确认问题局限于配置对象引用。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason: 1` (label: `reason="CreateContainerConfigError"`) | 监控数据客观验证了 Kubernetes 事件的状态。 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 0` (container: app) | 证实容器从未成功启动，排除了启动后崩溃重启的可能性。 |

**证据说明：**
Kubernetes 事件（#1）与容器等待状态（#2, #3）提供了完全一致的失败原因：Secret 中缺少 `unavailable-key`。Metric 数据（#6, #7）佐证了该状态已持续且无重启发生。配置信息（#5）确认非资源限制问题。由于容器未启动，Logging 和 Tracing 数据不可用，当前事实已闭环。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义引用 Secret 'workload-input' 中不存在的 key 'unavailable-key' → kubelet 无法解析容器配置 → 容器创建失败 (CreateContainerConfigError) → Pod 保持 Pending/Unready 状态
```

### 根因结论

**已确认根因：**
Pod `aiops-case-04/workload-6584f97c76-wvcb2` 的容器配置错误地引用了 Secret `workload-input` 中的键 `unavailable-key`，而该键在 Secret 中并不存在。

这一配置错误导致 kubelet 无法完成容器初始化配置，直接触发 `CreateContainerConfigError` 状态（证据 #1, #3）。容器因此从未启动，表现为持续处于 Pending 且未就绪状态（证据 #2, #4），且无重启计数（证据 #7）。该结论与 Metric 中的等待原因指标（证据 #6）完全印证，无需日志或链路数据即可确证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 19.1s
├─ 并发证据采集: 53.3s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 53.3s (Evidence 47.1s, RCA 6.1s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
