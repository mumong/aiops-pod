## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod 容器 spec 中引用了 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key`，而该 Secret 实际仅包含 key `available-key`，导致 kubelet 无法创建容器并持续抛出 `CreateContainerConfigError`。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason: "CreateContainerConfigError"` (fact-78169bd5d501) | 确定容器因配置错误停滞在等待状态 |
| 2 | K8s State | Kubernetes | `container.waiting_message: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input"` (fact-79de1c173a8e) | 直接指出缺少的密钥名及所在 Secret 名称 |
| 3 | K8s Event | Kubernetes | `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-95e579454176) | 确认 kubelet 持续失败的确切原因 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` 且 `reason="CreateContainerConfigError"` (fact-de4b9d87dfe5) | 验证 K8s 状态指标与容器错误状态一致 |

上述证据相互印证：容器因引用了 `aiops-case-04/workload-input` Secret 中不存在的 key `unavailable-key` 而无法启动。Metric 数据确认了该错误的持续性，且排除了其他状态（如 Failed 或 Running）。日志和链路数据因容器未启动而物理上不可用，但这不影响配置错误的定界。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 引用不存在的 Secret Key → 容器配置校验失败 → kubelet 抛出 CreateContainerConfigError → 容器无法启动并持续重试
```

### 根因结论

已确认根因为：**Pod 容器配置中错误引用了 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key`**。

该事实由 K8s State 和 Event 数据直接支撑（证据 #2, #3），Metric 数据确认了错误的持续存在（证据 #4）。由于容器因配置错误未能成功启动，日志和 Tracing 数据为空是预期行为，不构成证据不足。现有证据已充分说明故障原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 24.1s
├─ 并发证据采集: 36.4s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 36.4s (Evidence 31.0s, RCA 5.2s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
