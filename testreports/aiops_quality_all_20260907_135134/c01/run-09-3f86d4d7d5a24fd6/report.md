## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod aiops-case-01/workload-68c557d875-bsq52 处于 Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod `aiops-case-01/workload-68c557d875-bsq52` | `phase: Pending`, `nodeName: None` (fact-69745d1a78a7) | 确认 Pod 始终处于未调度状态 |
| 2 | K8s Event | default-scheduler | `FailedScheduling 18m` 消息: "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available..." (fact-2b6b874aaee8) | 直接指出失败原因为节点亲和性/选择器不匹配，且无法通过抢占解决 |
| 3 | K8s Config | Pod Spec (Container: app) | `requests: {cpu: 5m, memory: 8Mi}`, `limits: {cpu: 50m, memory: 32Mi}` (fact-0c950f027b7e) | 确认资源请求极小，排除因资源不足导致的调度失败 |
| 4 | Metric | kube_pod_status_phase | `phase=Running` 对应的值为 `0` (fact-0e10f193d99c) | 侧面印证无正常运行 Pod，与 K8s State 一致 |

**证据分析：**
K8s State 和 Event 共同锁定了 Pending 的根本原因是“节点亲和性/选择器不匹配”。K8s Config 确认了资源消耗极低，排除了资源竞争的可能。Metric 数据佐证了该工作负载处于未运行状态。日志与追踪因容器未启动而无数据，符合预期。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 配置了节点选择器 (如: aiops.lab/unavailable=true) → 集群中所有节点标签不匹配该选择器 → 调度器返回 FailedScheduling (0/3 nodes available) → Pod 保持 Pending 状态
```

### 根因结论

**已确认的根因**：Pod 的调度配置（节点选择器/亲和性规则）要求节点具备特定标签，但集群中所有 3 个节点均不满足该标签要求，导致默认调度器无法找到可用节点，Pod 被挂起（Pending）。
- **支持证据**：Event 明确报告 `node(s) didn't match Pod's node affinity/selector` (证据 #2)；Config 证明非资源问题 (证据 #3)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 30.0s
├─ 并发证据采集: 32.2s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 32.2s (Evidence 26.3s, RCA 5.8s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable, pod-volume-mount-failed
