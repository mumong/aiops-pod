## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 处于 Pending 状态，容器 app 报错 CreateContainerConfigError |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Metric | prometheus | `kube_pod_container_status_waiting_reason` for `aiops-case-v11/workload` (container: `app`) = 1, labels include reason=`CreateContainerConfigError` (fact-5ab368727825) | 证实容器当前处于因配置错误导致的 Waiting 状态，且未发生重启 |
| 2 | Metric | prometheus | `kube_pod_status_phase` for `kube-state-metrics` = 1 with phase=`Pending` (fact-b34a0d73cd2f); `kube_pod_container_status_restarts_total` for `app` = 0 (fact-a13aae4046e7) | 提供上下文：Pod 持续处于 Pending 状态且重启计数为 0，符合配置挂载失败而非运行时崩溃的特征 |
| 3 | K8s State | diagnosis | `diagnostic_status`: diagnosed, `status`: CreateContainerConfigError, `phenomenon`: Pod `aiops-case-v11/workload` 处于 Pending 状态，容器 `app` 报错 CreateContainerConfigError | 基础事实：确认了实体状态及异常原因标识符 |
| 4 | K8s Config | formal_rca | `root_cause`: Pod spec 错误引用了 ConfigMap 'workload-input' 中不存在的 key 'unavailable-key' | 直接归因：指明了具体的资源配置错误点 |

**证据关联分析**：
Prometheus 指标（fact-5ab368727825）直接提供了容器因配置错误进入 Waiting 状态的观测事实，且重启计数为 0（fact-a13aae4046e7），这与“配置引用错误”而非“运行时崩溃”的假设相符。K8s State 事实确认了当前的异常现象，而 RCA 定义的具体错误细节解释了该现象的成因。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 错误引用了 ConfigMap 'workload-input' 中不存在的 key 'unavailable-key' → kubelet 拉取配置时 KeyNotFound 异常 → 容器进入 Waiting 状态且 reason 为 CreateContainerConfigError → Pod 无法启动进入 Running 状态
```

### 根因结论

已确认的根因是 Pod 规范（spec）中错误引用了 ConfigMap `workload-input` 中不存在的 key `unavailable-key`。这一配置错误导致 kubelet 在尝试拉取配置时抛出 `KeyNotFound` 异常，进而使容器无法启动，停留在 Waiting 状态并返回 `CreateContainerConfigError` 原因，表现为 Pod 无法进入 Running 状态（引用证据编号 1, 3, 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 18.2s
├─ 并发证据采集: 53.1s
│  └─ g1 aiops-case-v11/workload: 53.1s (Evidence 44.4s, RCA 8.6s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
