## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod aiops-case-01/workload-68c557d875-gtzc8 处于 Pending 状态，未分配到节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-01/workload-68c557d875-gtzc8` 状态为 `Pending` | 确认为调度异常，未分配到节点 |
| 2 | K8s Event | Kubernetes | `FailedScheduling 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 明确指示调度失败原因是节点亲和性/选择器不匹配 |
| 3 | Metric | Prometheus | `kube_pod_status_phase` 值 `1` (phase=Pending)，无 `Failed` 状态 | 确认故障持续且未转为 CrashLoopBackOff 等运行态错误 |
| 4 | K8s Config | Kubernetes | 资源请求：CPU `5m`, Memory `8Mi`；资源限制：CPU `50m`, Memory `32Mi` | 资源请求极低，排除因资源不足导致调度拒绝的可能性 |

**证据互证说明：**
K8s 事件 (证据 2) 提供了调度的直接失败原因（亲和性不匹配），而资源配置事实 (证据 4) 排除了资源压力作为干扰因素。Pod 状态 (证据 1) 与 Metric 记录 (证据 3) 共同锁定了故障停留在调度阶段，未进入容器生命周期，进一步支持是调度约束导致的拒绝。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义配置 NodeSelector `aiops.lab/unavailable=true` → 集群所有节点缺失该标签 → 调度器因亲和性/选择器不匹配拒绝调度 → Pod 保持 Pending 状态
```

### 根因结论

已确认根因为 **Pod 节点选择器（NodeSelector）配置与实际集群节点标签不匹配**。

Pod 定义中要求节点必须包含标签 `aiops.lab/unavailable=true`，但集群中所有可用节点均不具备该标签。这导致 `default-scheduler` 在调度时无法找到符合条件的节点，直接引发 `FailedScheduling` 事件（证据 2），致使 Pod 一直处于 `Pending` 状态（证据 1）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 16.3s
├─ 并发证据采集: 66.2s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 66.2s (Evidence 57.1s, RCA 9.0s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
