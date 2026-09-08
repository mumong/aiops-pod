## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-7ds5p 处于 Pending 状态，容器 app 处于 CreateContainerConfigError 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | pod `aiops-case-04/workload-6584f97c76-7ds5p` 当前状态 `Pending` (fact-1db3715cea05) | 确认 Pod 未处于运行状态，排除业务层面的波动，定位至启动阶段。 |
| 2 | K8s Event | Kubernetes | `Failed` 事件：`Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-e69ffea52ad2) | 直接指出 Pod 启动失败的底层机制原因（Secret 键值缺失）。 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 `1`，且 `reason: CreateContainerConfigError` (fact-ee27fbef2cc4) | 量化确认了 Pod 处于配置错误等待状态，与 K8s 事件日志相互印证。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 值为 `0` (fact-b4c42bd4f329) | 说明该问题导致容器未能尝试启动，属于一次性配置失败，非运行时故障。 |

**证据说明：**
1. Kubernetes Event (2) 中的 `CreateContainerConfigError` 原因与 Prometheus Metric (3) 中的 `reason: CreateContainerConfigError` 标签完全一致，排除了偶发性网络或资源问题。
2. Pod 状态 (1) 为 `Pending` 且重启次数 (4) 为 0，进一步证实了故障发生在调度完成后的容器创建阶段，因无法加载 Secret 配置而阻塞。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 缺少期望的 key → 容器配置加载失败 → 创建容器步骤报错 → 持续处于 CreateContainerConfigError
```

### 根因结论

已确认根因为 Pod 配置引用了不存在的 Secret 密钥。具体表现为 Pod 配置中请求加载 Secret `aiops-case-04/workload-input` 下的 `unavailable-key`，而该 Key 在 Secret 中不存在，导致 kubelet 拒绝创建容器 [证据 2, 3]。现有证据（事件日志与 Metric 状态）已足以闭环验证该配置缺失导致 Pod 无法启动的结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 24.2s
├─ 并发证据采集: 42.5s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 42.5s (Evidence 35.0s, RCA 7.3s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
