## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod 配置中引用了 Secret 'workload-input' 中不存在的 key 'unavailable-key' 且 optional 为 false，导致 kubelet 创建容器时失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (fact-94453ecaee6c) | `container.waiting_message`: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input" | 确证 kubelet 在容器启动阶段报出的致命配置错误。 |
| 2 | K8s Event | kubernetes (fact-b5f69a451602) | `event.message`: "Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input" (x12 over 57m) | 佐证该错误非瞬时现象，已持续且反复触发。 |
| 3 | K8s State | kubernetes (fact-dfd6a9aa588a) | `container.waiting_reason`: "CreateContainerConfigError" | 明确异常终止状态，该状态仅由挂载资源缺失等初始化失败引起。 |
| 4 | K8s State | kubernetes (fact-bd2617545a01) | `pod.phase`: "Pending" | 反映 Pod 始终停留在初始化阶段，未能进入 Running 状态。 |
| 5 | Metric | prometheus (fact-6bbde43543c6) | `kube_pod_container_status_waiting_reason`: 1 (labels: `reason=CreateContainerConfigError`) | 独立于 K8s API 的监控数据，确证当前等待原因确实为 `CreateContainerConfigError`。 |

**证据综合分析**：
K8s API 直接报告了容器等待消息（#1）及重复的 K8s 事件（#2），明确指向在 `workload-input` 这个 Secret 中找不到名为 `unavailable-key` 的 Key。这一具体错误信息完美解释了 `CreateContainerConfigError` 状态（#3）和 Pod 处于 Pending 阶段（#4）的现象。Prometheus 监控数据（#5）从独立观测维度进一步确证了 `CreateContainerConfigError` 是当前唯一的容器等待原因，排除了其他网络或调度问题的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 配置了 optional=false 的 secretKeyRef 引用 'unavailable-key' (隐含事实) 
→ kubelet 校验 Secret 'workload-input' 缺失该 Key (机制) 
→ 触发 CreateContainerConfigError (直接失败) 
→ Pod 状态卡死在 Pending (用户可见现象)
```

### 根因结论

已确认根因：Pod 的配置引用了 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key`，且配置为不可忽略（optional=false），导致 kubelet 在创建容器前校验失败，进而引发 `CreateContainerConfigError` 及 Pod 状态停滞。

证据支撑包括 K8s 的报错消息 (证据 #1, #2)、容器等待状态 (证据 #3) 以及监控中的对应指标 (证据 #5)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 19.8s
├─ 并发证据采集: 48.0s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 48.0s (Evidence 40.4s, RCA 7.5s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
