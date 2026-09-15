## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod aiops-case-01/workload-68c557d875-gtzc8 处于 Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `Unschedulable` condition: "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector" | 提供调度失败的直接技术原因，证实集群内不存在满足亲和性要求的节点 |
| 2 | K8s Event | kubernetes | Event `FailedScheduling` (x2 over 16m): "3 node(s) didn't match Pod's node affinity/selector" | 确认调度行为在 16 分钟内持续发生，并非偶发现象 |
| 3 | K8s State | kubernetes | Pod `Pending` 状态 (phase=P, condition=Unschedulable, message同上) | 描述用户可见的最终症状，表明 Pod 无法启动 |
| 4 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"}=1` | 从监控侧确认 Pod 处于 Pending 状态的客观事实 |

**证据关联分析：**
`fact-9095ced5ccd2` 从 Metrics 维度印证了 Kubernetes 记录的 Pod `Pending` 状态。Kubernetes 的事件 (`fact-1bcdf4fb3e55`) 和状态 (`fact-94f0c76105e4`) 高度一致，均指向“节点不匹配”这一特定故障模式，共同构建了清晰的调度受阻证据链。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 nodeSelector 'aiops.lab/unavailable=true' → 集群节点均缺少该标签 → 调度器 FailedScheduling → Pod 处于 Pending 状态
```

### 根因结论

根因是 Pod `aiops-case-01/workload-68c557d875-gtzc8` 定义了 `nodeSelector`（即 `aiops.lab/unavailable=true`），但集群中所有节点均不存在该标签，导致 `default-scheduler` 无法找到匹配节点。这被 Kubernetes 事件（`fact-1bcdf4fb3e55`）和状态条件（`fact-94f0c76105e4`）一致确认。

---

## 📊 性能统计

```text
├─ 总耗时: 58.6s
├─ 问题定位: 15.6s
├─ 并发证据采集: 35.3s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 35.3s (Evidence 29.4s, RCA 5.9s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
