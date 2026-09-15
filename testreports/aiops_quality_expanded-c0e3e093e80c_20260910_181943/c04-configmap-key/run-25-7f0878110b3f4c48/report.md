## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v11/workload` | CreateContainerConfigError | Pod aiops-case-v11/workload 处于 Pending 状态，容器 app 因 CreateContainerConfigError 无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Error: couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` (发生 12 次，间隔 45m) | 直接指出配置挂载缺失导致的容器创建失败机制 |
| 2 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1, reason: `CreateContainerConfigError` | 从指标侧独立确认了容器的特定失败状态 |
| 3 | K8s State | kubernetes | Pod `aiops-case-v11/workload` 状态 `Pending` | 确认应用尚未进入运行生命周期 |
| 4 | Metric | prometheus | `kube_pod_status_phase` (Pod: Pending) = 1, (Container: Running) = 0 | 确认集群层面该工作负载未成功调度至 Running 状态 |
| 5 | K8s Config | kubernetes | Pod `app` 容器配置 Request: 8Mi/5m; Limit: 32Mi/50m | 确认资源配额配置正常，排除资源不足导致的调度阻塞 |
| 6 | K8s State | kubernetes | `container.restart_count` = 0 | 确认 Pod 始终未启动，处于持续重试创建阶段 |

**证据关联与印证：**
Kubernetes 事件 (证据#1) 提供了确切的配置缺失原因，与 K8s 状态 (证据#3) 和 Metric 指标 (证据#2) 中观测到的 `CreateContainerConfigError` 及 `Pending` 状态完全一致。由于容器始终处于 `Pending` 状态且重启次数为 0 (证据#6)，日志和追踪维度 (Logging/Tracing) 因物理上无法启动而判定为 `not_applicable`，不存在跨维度的冲突或独立补充证据。

## 🎯 根因分析 · g1

```text
ConfigMap 'aiops-case-v11/workload-input' 中缺少 Key 'unavailable-key' → Kubelet 挂载配置失败 → 容器创建报错 CreateContainerConfigError → Pod 处于 Pending 状态且应用未运行
```

**根因结论：**
已确认根因为 **Pod 定义中引用的 ConfigMap 缺少所需 Key**。证据显示 kubelet 多次尝试启动容器均因 `couldn't find key unavailable-key in ConfigMap aiops-case-v11/workload-input` 而失败（事实 ID: `fact-7ff24252c60e`），并直接导致了 `CreateContainerConfigError` 状态（事实 ID: `fact-a619096a31c1`）。由于配置挂载失败发生在容器生命周期之前，未产生任何应用日志或流量（日志/追踪维度不适用）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 13.1s
├─ 并发证据采集: 38.3s
│  └─ g1 aiops-case-v11/workload: 38.3s (Evidence 30.6s, RCA 7.7s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v11/workload**: pod-config-error
