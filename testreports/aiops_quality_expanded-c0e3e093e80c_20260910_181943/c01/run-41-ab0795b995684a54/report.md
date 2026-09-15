## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod 配置了 nodeSelector 'aiops.lab/unavailable=true'，但集群中所有可用节点（master, node1, node2）均缺少该标签，导致调度器无法将 Pod 调度到任何节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Condition | `type=PodScheduled, status=False, reason=Unschedulable` (fact-9d0844190189) | 确定 Pod 目前处于不可调度状态 |
| 2 | K8s State | Pod Phase | `phase=Pending` (fact-f98d1bcb3142) | 确认 Pod 尚未被调度到任何节点 |
| 3 | K8s Event | Scheduler | `FailedScheduling` (fact-42d3a29133d8) | 直接说明调度器因节点不匹配而放弃调度 |
| 4 | K8s Config | Pod Spec | `container.resource_request.cpu=5m, memory=8Mi` (fact-80fb1301db74, fact-16c4de2299d4) | 排除资源容量不足导致调度的可能性，佐证为节点标签问题 |
| 5 | K8s Config | Pod Spec | `container.resource_limit.cpu=50m, memory=32Mi` (fact-679198acc696, fact-7c89e53bafdb) | 进一步确认资源需求极低，非资源瓶颈 |
| 6 | Metric | Prometheus | `kube_pod_status_phase{phase="Pending"}=1` (fact-7224826da2cc) | 独立确认了 Pod 的 Pending 状态持续存在 |

证据 1、2、3 相互印证：调度器报告 `FailedScheduling`，Pod 状态反映为 `Unschedulable` 且处于 `Pending` 阶段，且错误信息明确指出是 `didn't match Pod's node affinity/selector`。资源请求指标（证据 4、5）极低，排除资源耗尽干扰；Metric 指标（证据 6）从监控系统角度独立确认了 `Pending` 状态的持续存在。日志和追踪数据因 Pod 未启动而不适用，无冲突。

## 🎯 根因分析 · g1

### 因果链

```text
节点缺乏指定标签 → 调度器节点选择器匹配失败 → Pod 无法被分配节点 → Pod 处于 Pending 状态
```

### 根因结论

已确认的根因是：Pod `workload-68c557d875-gtzc8` 配置了 `nodeSelector 'aiops.lab/unavailable=true'`，但集群中所有可用节点（master, node1, node2）均缺少该标签。

该根因直接导致了调度器在 `FailedScheduling` 事件（证据 3）中报告的 `didn't match Pod's node affinity/selector` 失败机制。由于节点不满足调度条件，Pod 被迫停留在 `Pending` 阶段（证据 1、2、6），无法进入运行状态。该结论由 Kubernetes 事件、Pod 状态配置直接支撑，无需补充日志或追踪数据。

---

## 📊 性能统计

```text
├─ 总耗时: 59.6s
├─ 问题定位: 18.8s
├─ 并发证据采集: 31.0s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 31.0s (Evidence 26.9s, RCA 4.0s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
