## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod 配置了 nodeSelector {aiops.lab/unavailable: true}，但集群中所有节点均未携带该 Label，导致调度器因亲和性/选择器不匹配而拒绝调度，Pod 持续处于 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.condition` | `PodScheduled: False, reason: Unschedulable, message: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 确认 Pod 无法被调度的直接事实原因，与事件日志一致 |
| 2 | K8s Event | `event.message` | `Warning FailedScheduling ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 调度器视角的直接报错，佐证调度失败的必然性 |
| 3 | Metric | `kube_pod_status_phase` | `Pending: 1, Running: 0` | 指标状态确证 Pod 长期处于未调度状态，未发生任何运行时转变 |
| 4 | K8s Config | `container.resource_request/limit` | CPU Request `5m`, Memory Request `8Mi` | 排除资源资源请求过大导致无法找到足够资源节点的可能性 |

**证据小结**：
状态（#1）与事件（#2）双重确认了“未匹配 Node Selector”是导致调度失败的唯一直接原因；指标（#3）证实了该状态已持续并占据 Pod 生命周期。资源请求（#4）数值极小，排除资源不足干扰。日志与 Tracing 因 Pod 未启动且无 IP，物理上不可用，与调度失败的结论不冲突。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 设置 nodeSelector 要求 aiops.lab/unavailable=true → 集群现有节点均无此 Label → 调度器拒绝调度(0/3 nodes match) → Pod 状态保持 Pending
```

### 根因结论

**已确认的根因**：Pod 配置了 `nodeSelector` 要求节点标签 `aiops.lab/unavailable: true`，但集群中所有节点（0/3）均未携带该 Label（引用证据 #1、#2）。这导致调度器因亲和性选择器不匹配而永久拒绝调度，使 Pod 持续处于 Pending 状态。资源请求量（#4）在阈值内，不属本次故障主因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.3s
├─ 并发证据采集: 38.0s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 38.0s (Evidence 31.1s, RCA 6.8s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
