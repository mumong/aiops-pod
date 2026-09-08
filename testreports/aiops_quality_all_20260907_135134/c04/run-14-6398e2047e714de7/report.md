## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod workload-6584f97c76-7ds5p 持续处于 CreateContainerConfigError 状态，容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Failed Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (x12 over 24m) | 确认 Kubelet 尝试创建容器时，因缺失 Secret key 而报错的具体原因 |
| 2 | K8s State | Kubernetes | `container.waiting_reason: CreateContainerConfigError`, `waiting_message: couldn't find key unavailable-key` | 确认容器的核心异常状态及具体的等待原因 |
| 3 | K8s State | Kubernetes | `pod.condition.Ready: False (ContainersNotReady: [app])`, `pod.phase: Pending` | 证实 Pod 因容器无法启动而持续处于不健康状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 `1`，标签 `reason: CreateContainerConfigError` | 验证 Kubernetes 集群层面的容器状态与异常现象一致 |

以上证据相互印证：Kubernetes Event 与 Container State 共同指出具体的配置错误（Secret 缺失 key），Metric 从集群监控角度确认了该异常状态的客观存在。Logging 与 Tracing 因容器未启动而缺失，属于预期内的观测盲区。

## 🎯 根因分析 · g1

### 因果链

```text
Secret aiops-case-04/workload-input 中缺失 key 'unavailable-key' → Pod spec 要求挂载该 key 到环境变量 → Kubelet 因找不到 key 报错并拒绝创建容器 → Pod 持续处于 CreateContainerConfigError 且 Pending 状态
```

### 根因结论

已确认的根因为：Pod spec 引用了 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key`，但该 Secret 中不存在此 key，导致 Kubelet 无法注入环境变量而拒绝创建容器。

该结论由事实支撑：
- **机制与直接失败**：`fact-9a5bd9501cd0` (K8s Event) 和 `fact-ca4dcc7bd58d` (K8s State) 明确记录了 Kubelet 报出 `"couldn't find key unavailable-key"` 的错误。
- **异常状态确认**：`fact-fcb85898ad81` 和 `fact-5d28dccf5d25` (Metric) 确认了容器处于 `CreateContainerConfigError` 状态。
- **现象佐证**：`fact-6f27b3c9b051` 等相关记录显示 Pod 处于 `Pending` 且 `Ready: False`，且 `fact-055e3d74ef88` 确认重启次数为 0，符合配置错误导致无法启动的特性。

---

## 📊 性能统计

```text
├─ 总耗时: 52.6s
├─ 问题定位: 12.7s
├─ 并发证据采集: 30.5s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 30.5s (Evidence 23.7s, RCA 6.8s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
