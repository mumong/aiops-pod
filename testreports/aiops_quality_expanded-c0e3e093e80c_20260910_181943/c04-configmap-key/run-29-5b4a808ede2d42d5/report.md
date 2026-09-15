## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 处于 CreateContainerConfigError 状态，容器启动失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod status: `Pending` (fact-9eec70c491f) | 确认 Pod 未进入运行态，处于等待配置阶段 |
| 2 | K8s Event | Kubernetes | `Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` (fact-967849b5178d, 47m 内重复 12 次) | 直接指明容器配置解析的具体失败原因 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` `reason=CreateContainerConfigError` (fact-b2998e8bde34) | 独立验证了 K8s 诊断的分类状态 |
| 4 | K8s Config | Kubernetes | Memory Limit: `32Mi` (fact-2e353f2c299c) | 排除内存限制导致容器启动失败的可能性 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` `0` (fact-654468adaf95) | 排除容器已启动后崩溃重启的情况 |

**证据互证分析：**
Kubernetes Event 直接指出了 `ConfigMap` 中缺少引用 Key 的具体错误，与 Metric 中显示的 `CreateContainerConfigError` 等待原因完全一致（证据 2 和 3）。K8s State 显示的 `Pending` 状态以及 Metric 中的重启次数为 0（证据 1、4 和 5）证实故障发生在启动前置阶段，而非运行后异常。配置资源（Memory Limit）的存在排除了资源限制导致的启动失败。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 配置引用了不存在的 ConfigMap Key -> Kubelet 无法解析环境变量配置 -> 容器创建阶段被拒绝 -> Pod 处于 CreateContainerConfigError 状态
```

### 根因结论

**已确认的根因：** Pod 配置文件引用了 ConfigMap `aiops-case-v11/workload-input` 中不存在的 Key `unavailable-key`。

**证据支撑：**
Kubernetes Event 记录明确显示 `Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input`，且该事件在 49 分钟内重复了 12 次。这直接导致了 `CreateContainerConfigError` 状态，并被 Prometheus 指标独立印证。故障发生在容器启动前的配置解析阶段，与重启次数为 0 的事实相符。

---

## 📊 性能统计

```text
├─ 总耗时: 50.0s
├─ 问题定位: 17.5s
├─ 并发证据采集: 23.8s
│  └─ g1 aiops-case-v11/workload: 23.8s (Evidence 16.8s, RCA 6.8s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
