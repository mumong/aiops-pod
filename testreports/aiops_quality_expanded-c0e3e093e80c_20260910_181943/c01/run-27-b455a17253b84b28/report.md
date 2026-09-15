## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod workload-68c557d875-gtzc8 处于 Pending 状态，未调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod.phase: Pending | 确认 Pod 未进入运行态的事实 |
| 2 | K8s State | kubernetes | PodScheduled=False, reason=Unschedulable, message="0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector..." | 直接展示调度失败原因：节点亲和性/选择器不匹配 |
| 3 | K8s Config | kubernetes | container.app resource_requests: cpu=5m, memory=8Mi | 提供资源需求上下文，排除资源不足导致的调度失败 |
| 4 | K8s Config | kubernetes | container.app resource_limits: cpu=50m, memory=32Mi | 提供资源上限上下文 |
| 5 | Metric | prometheus | kube_pod_status_phase{phase="Pending"}=1 (11:06:11Z) | 独立观测确认 Pod 持续处于 Pending 状态 |
| 6 | Metric | prometheus | kube_pod_status_phase{phase="Unknown"}=0 | 排除 Pod 状态不明确的可能 |

**证据关系说明**：
1. `fact-8e09bd3cbaeb` (K8s Event) 明确指出调度失败的直接原因是节点不匹配“Pod's node affinity/selector”；
2. `fact-56bb7b1215b4` 和 `fact-e933fa0f5bd7` (K8s Config) 显示该 Pod 的资源请求极低（CPU 5m / Mem 8Mi），佐证了调度失败并非因资源不足；
3. `fact-a5b383528ef7` (Metric) 与 K8s 状态一致，共同验证 Pod 长时间处于 Pending 状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 包含 nodeSelector: {aiops.lab/unavailable: true} → 集群节点缺乏匹配标签 → 调度器触发 FailedScheduling 事件 → Pod 保持 Pending 状态
```

### 根因结论

已确认的根因为 **调度策略配置错误**：
- Pod 定义了 `nodeSelector` 要求节点具备 `aiops.lab/unavailable=true` 标签；
- 集群中 3 个节点均无此标签，导致调度器无法分配 Pod。

证据支持：
- `fact-8e09bd3cbaeb` 记录调度器因 `node affinity/selector` 不匹配而判定 `Unschedulable`；
- `fact-56bb7b1215b4`、`fact-e933fa0f5bd7`、`fact-1b2be829ab0b`、`fact-ca48032f9885` 排除了资源限制导致的调度失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 23.5s
├─ 并发证据采集: 33.4s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 33.4s (Evidence 27.1s, RCA 6.2s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
