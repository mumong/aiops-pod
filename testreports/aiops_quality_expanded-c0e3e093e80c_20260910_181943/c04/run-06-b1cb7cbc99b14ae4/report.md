## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-h4lt9 处于 CreateContainerConfigError 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Failed ... kubelet Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` | 核心证据：明确指出 Secret 卷中引用键 `unavailable-key` 缺失，直接导致容器创建错误 |
| 2 | K8s State | Kubernetes | Pod 状态 `Pending`，且 `restart_count` 为 0 | 确认故障发生在启动配置阶段，无应用运行迹象 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (labels: `reason=CreateContainerConfigError`) | 独立观测：PromQL 指标确认容器处于配置错误等待状态，与 K8s Event 一致 |
| 4 | K8s Config | Kubernetes | Container `app` 资源上限：`cpu=50m`, `memory=32Mi`；资源请求：`cpu=5m`, `memory=8Mi` | 排除资源超限（OOM/CPUThrottling）导致的异常，确认为配置项问题 |

**证据互证：**
Kubernetes Event (`#1`) 提供了最直接的错误语义，表明 `Secret` 引用失败；`#2` 和 `#3` 分别从 Pod 状态和 Prometheus 指标层面印证了 `CreateContainerConfigError` 现象，三者指向同一根因，且 `#4` 的资源配置进一步排除了其他调度或运行时资源竞争的可能。

## 🎯 根因分析 · g1

### 因果链

```text
Pod manifest 错误引用 Secret key 'unavailable-key' → kubelet 挂载卷时键不存在导致配置校验失败 → 触发 CreateContainerConfigError 异常 → Pod 持续处于 Pending 状态
```

### 根因结论

**已确认的根因**：Pod `aiops-case-04/workload-6584f97c76-h4lt9` 启动失败的根本原因是其挂载的 Secret 卷中引用了不存在的键 `unavailable-key`（证据 `#1`）。

这一配置错误直接触发了 kubelet 的 `CreateContainerConfigError` 状态，阻止了容器的初始化。该结论由 K8s Event (`#1`) 明确支持，并由 K8s State (`#2`) 和 Prometheus 指标 (`#3`) 的观测结果交叉验证，排除了资源限制或网络等其他常见故障因素。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 19.9s
├─ 并发证据采集: 64.5s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 64.5s (Evidence 58.3s, RCA 6.2s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-h4lt9**: pod-config-error
