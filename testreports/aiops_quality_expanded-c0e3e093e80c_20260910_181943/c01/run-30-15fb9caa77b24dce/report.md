## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod workload-68c557d875-gtzc8 in aiops-case-01 remains in Pending state with FailedScheduling |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.condition` | `PodScheduled=False, reason=Unschedulable, message="3 node(s) didn't match Pod's node affinity/selector"` | 确认为调度失败，非健康状态异常 |
| 2 | K8s Config | `container.resource_limit.cpu` | `50m` | 确认请求未触及节点资源硬限制边界 |
| 3 | K8s Event | `event.message` | `"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"` | 直接指出所有可用节点均未通过亲和性检查 |
| 4 | K8s Event | `event.message` | `"Preemption is not helpful for scheduling"` | 排除资源争抢可能性，判定为硬性约束不匹配 |

**证据印证说明：**
*   K8s 事件 #2 与 #3 共同表明调度器在 3 个节点上均执行了亲和性/选择器检查并全部失败。
*   由于 #3 指出抢占（Preemption）无效，且 #4 显示资源请求量极小，排除了资源不足导致驱逐或抢占的可能，进一步确认问题源于节点标签匹配。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了节点选择器约束 (nodeSelector) → 集群内 3/3 节点均缺失对应的标签/不满足选择器条件 → 调度器判定所有节点亲和性检查失败 → Pod 保持 Pending 状态，无法调度
```

### 根因结论

**已确认的根因：**
调度失败是由**节点亲和性（Node Affinity/Selector）不匹配**导致的。Pod 被配置了严格的节点选择器要求（如 `aiops.lab/unavailable=true`），但集群中现有的 3 个节点均不满足该标签选择器条件，导致 `default-scheduler` 判定所有节点不可用。

此结论由证据 #1（状态为 Unschedulable）、#2（明确的节点匹配失败记录）以及 #3（抢占无效，排除资源争抢）共同支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 15.7s
├─ 并发证据采集: 62.8s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 62.8s (Evidence 55.5s, RCA 7.3s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
