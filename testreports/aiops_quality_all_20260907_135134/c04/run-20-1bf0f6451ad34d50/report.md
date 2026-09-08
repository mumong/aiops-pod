## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-7ds5p` | CreateContainerConfigError | Pod Spec 中引用了 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key`，而该 Secret 实际仅包含 key `available-key`，导致容器配置加载失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Container `app` waiting reason: `CreateContainerConfigError` (fact-91e888382611) | 确认当前处于配置加载失败状态 |
| 2 | K8s State | kubernetes | Container `app` waiting message: `couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-273bbc9f00e0) | 明确指出导致失败的错误原因和缺失键 |
| 3 | K8s State | kubernetes | Pod phase: `Pending` (fact-346fa41594a6) | 展示异常组的状态表现 |
| 4 | K8s Config | kubernetes | Container `app` resource request: `cpu=5m`, `memory=8Mi` (fact-87d9cb86a10a, fact-a4a99a5ba7c4) | 提供资源请求配置上下文 |
| 5 | K8s Config | kubernetes | Container `app` resource limit: `cpu=50m`, `memory=32Mi` (fact-e77b93d5c1d3, fact-0859008aec64) | 提供资源限制配置上下文 |
| 6 | K8s State | kubernetes | Pod condition `Ready=False`, reason `ContainersNotReady` (fact-98f7f9720ce9) | 确认 Pod 就绪状态受 Container 状态影响 |
| 7 | K8s State | kubernetes | Pod condition `Initialized=True`, `PodScheduled=True` (fact-4343a35611b5, fact-ff6859619d30) | 排除资源调度与初始化阶段的异常 |
| 8 | K8s State | kubernetes | Container `app` restart count: `0` (fact-ea28b2ed1bc6) | 确认容器尚未发生过重启 |
| 9 | Metric | prometheus | `kube_pod_container_status_waiting_reason` for `CreateContainerConfigError` is `1` (fact-6e5cc87b6c1e) | 独立验证容器处于配置错误等待状态 |
| 10 | Metric | prometheus | `kube_pod_status_phase` for `Pending` is `1` (fact-07a68669932b) | 独立验证 Pod 处于 Pending 状态 |
| 11 | Metric | prometheus | `kube_pod_container_status_restarts_total` for `app` is `0` (fact-7bb8072d196b) | 独立验证容器无重启历史 |

**证据关联说明**：
Kubernetes 事实 (fact-273bbc9f00e0) 直接给出了无法加载 Secret 的错误原文，这是导致 `CreateContainerConfigError` 的直接原因。Metric 数据 (fact-6e5cc87b6c1e, fact-07a68669932b) 独立确认了 Pod 与容器的等待状态与 K8s 控制面报告的现象一致。资源配置事实证明不存在资源不足导致的 Pending 问题。Logging 与 Tracing 因容器未启动而不可用。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key` → 容器配置加载失败 → CreateContainerConfigError 异常 → Pod 处于 Pending 状态
```

### 根因结论

已确认根因为 Pod Spec 中引用了 Secret `aiops-case-04/workload-input` 中不存在的 key `unavailable-key`。该配置错误导致 Kubelet 无法完成容器配置加载，直接触发 `CreateContainerConfigError` 状态，使 Pod 保持 Pending。该结论由 K8s 事件信息 (fact-273bbc9f00e0) 与 Prometheus 指标数据 (fact-6e5cc87b6c1e) 相互印证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 13.6s
├─ 并发证据采集: 41.0s
│  └─ g1 aiops-case-04/workload-6584f97c76-7ds5p: 41.0s (Evidence 36.2s, RCA 4.7s)
└─ 汇总总结: 13.7s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-7ds5p**: pod-config-error
