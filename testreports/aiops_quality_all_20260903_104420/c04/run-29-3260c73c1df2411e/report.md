## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-wvcb2` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-wvcb2 处于 Pending 状态，容器 app 因 CreateContainerConfigError 未能启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input` (fact-07d3aa4ee12f) | 直接指出 Secret 中缺少预期 key |
| 2 | K8s State | Kubernetes | `container.waiting_reason`: `CreateContainerConfigError` (fact-2f0015c6bb45) | 确认容器因配置问题无法创建 |
| 3 | K8s State | Kubernetes | `pod.status`: `Pending` (fact-bf66c187ac07) | 确认 Pod 处于挂起状态，未进入运行态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CreateContainerConfigError"}` = `1` (fact-6a2168af13b4) | 独立印证容器因配置错误处于等待状态 |

**证据分析：**
Kubernetes 事件与状态事实明确指向了 Secret key 缺失导致容器无法启动，Metrics 数据作为独立观测源确认了这一状态（waiting_reason 为 CreateContainerConfigError 且值为 1）。由于容器未启动，Logging 与 Tracing 维度因物理上无应用日志和流量而不适用，但这并不影响基于 K8s 底层状态判断的准确性。

## 🎯 根因分析 · g1

### 因果链

```text
Secret aiops-case-04/workload-input 缺少 key unavailable-key → kubelet 无法挂载配置导致 CreateContainerConfigError → Pod 持续处于 Pending 状态 → 业务不可用
```

### 根因结论

已确认的根因是 Pod 的 Spec 中配置引用了 Secret `aiops-case-04/workload-input` 中的 key `unavailable-key`，但该 key 在 Secret 中实际不存在（导致 kubelet 报错）。这一配置缺失直接引发了 `CreateContainerConfigError`，使容器无法创建，Pod 因此一直维持在 `Pending` 状态，无法提供服务。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 16.7s
├─ 并发证据采集: 48.5s
│  └─ g1 aiops-case-04/workload-6584f97c76-wvcb2: 48.5s (Evidence 39.9s, RCA 8.4s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-04/workload-6584f97c76-wvcb2**: pod-config-error
