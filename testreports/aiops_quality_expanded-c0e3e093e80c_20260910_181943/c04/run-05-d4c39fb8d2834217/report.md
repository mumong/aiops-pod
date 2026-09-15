## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-04/workload-6584f97c76-h4lt9` | CreateContainerConfigError | Pod aiops-case-04/workload-6584f97c76-h4lt9 状态为 Pending，Container 状态为 CreateContainerConfigError。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: CreateContainerConfigError | 判定容器无法启动的直接状态。 |
| 2 | K8s State | kubernetes | `container.waiting_message`: "couldn't find key unavailable-key in Secret aiops-case-04/workload-input" | 指明缺失资源对象的具体错误原因。 |
| 3 | K8s Event | kubernetes | Warning Failed (x12 over 15m): "Error: couldn't find key unavailable-key in Secret aiops-case-04/workload-input" | 确证 kubelet 反复尝试失败的事实及发生频率。 |
| 4 | K8s State | kubernetes | `pod.status`: Pending, `pod.condition`: ContainersReady=False | 描述 Pod 持续不可用的宏观状态。 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason: CreateContainerConfigError) | 监控指标层面确认 Pod 处于配置错误等待状态。 |

**证据分析：**
Kubernetes 的状态记录（事实 1-4）与 Prometheus 监控指标（事实 5）完全吻合，共同指向容器因配置错误被阻塞。日志与追踪系统未采集到数据，是因为容器在启动前即报错退出，无法生成应用层面的运行日志，符合物理限制。

## 🎯 根因分析 · g1

### 因果链

```text
Secret `aiops-case-04/workload-input` 缺少 key `unavailable-key` → 配置挂载失败导致 CreateContainerConfigError → Pod 处于 Pending 状态，容器不运行
```

### 根因结论

已确认的根因是：Secret `aiops-case-04/workload-input` 中不存在 Pod 配置所需引用的 key `unavailable-key`（证据 1, 2, 3）。这直接导致 kubelet 无法完成容器配置并抛出 `CreateContainerConfigError`，从而使 Pod 停留在 Pending 状态（证据 4, 5）。

---

## 📊 性能统计

```text
├─ 总耗时: 54.6s
├─ 问题定位: 14.5s
├─ 并发证据采集: 33.0s
│  └─ g1 aiops-case-04/workload-6584f97c76-h4lt9: 33.0s (Evidence 25.2s, RCA 7.7s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- 未调用 Runbook
