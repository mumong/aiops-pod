## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod nodeSelector 配置了标签 `aiops.lab/unavailable: true`，但集群中没有任何节点拥有此标签，导致调度器无法找到匹配节点。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` (fact-3e5a7ac9b25a) | `FailedScheduling`：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` (持续 4m40s，x13 次) | 证明调度器在集群中找不到满足条件的节点，是调度的直接失败原因 |
| 2 | K8s State | `pod.condition` (fact-4a1da4fa6d6d) | `PodScheduled=False`，`reason=Unschedulable`，`message` 同上 | 确认 Pod 目前处于未调度状态，且原因与 Event 记录一致 |
| 3 | K8s Config | `container.resource_request.cpu` (fact-2ddac33796fe) | `5m` | 资源需求极低，排除因计算资源不足导致的调度阻塞 |
| 4 | K8s Config | `container.resource_limit.memory` (fact-3379fc699cdc) | `32Mi` | 内存限制正常，排除因内存资源问题导致的调度阻塞 |
| 5 | K8s State | `pod.status` (fact-8bac0d101596) | `Pending` | 确认 Pod 处于 Pending 阶段，未进入运行状态 |
| 6 | Metric | `kube_pod_status_phase` (fact-f02a83eb46c2) | `Pending`，`sample_count=1` | Prometheus 数据确认当前阶段为 Pending，与 K8s 状态一致 |
| 7 | Metric | `kube_pod_status_phase` (fact-7c877c2d7489) | `Failed`，`value=0` | 排除因 Pod 崩溃或进入 Failed 状态导致的现象，明确处于 Pending 期 |

**证据关系与结论：**
1. `fact-3e5a7ac9b25a` (Event) 和 `fact-4a1da4fa6d6d` (Condition) 从调度日志和 Pod 状态两个维度一致指向同一失败原因：“没有节点匹配 Pod 的亲和性/选择器”。
2. `fact-f02a83eb46c2` 和 `fact-7c877c2d7489` 验证了 Pod 目前处于 `Pending` 状态，而非 `Running` 或 `Failed`。
3. 资源类事实 (`fact-2ddac33796fe`, `fact-3379fc699cdc`) 证明该 Pod 资源需求极低，不存在因资源不足（如 CPU/Memory 不够）被拒绝的情况。
4. Logging 和 Tracing 因 Pod 未启动而 `not_applicable`，符合预期，不影响对调度失败原因的判断。
5. 诊断信息指出 `nodeSelector` 配置了 `aiops.lab/unavailable: true`，且集群无此标签节点，与 K8s Event 中“未匹配节点亲和性/选择器”的描述完全吻合。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了不存在于任何节点上的 nodeSelector (`aiops.lab/unavailable: true`) → 调度器无法匹配任何节点 (0/3) → 触发 FailedScheduling Event → Pod 处于 Pending 状态
```

### 根因结论

**已确认的根因：** Pod `aiops-case-01/workload-68c557d875-gtzc8` 的 `nodeSelector` 或节点亲和性配置了标签 `aiops.lab/unavailable: true`，但集群中没有任何节点拥有此标签，导致调度器无法找到匹配节点。

- **证据支持：** 
  - `fact-3e5a7ac9b25a` (Event) 和 `fact-4a1da4fa6d6d` (Condition) 明确记录调度失败原因为“节点未匹配 Pod 的亲和性/选择器”。
  - 诊断信息中明确指出配置了 `nodeSelector: aiops.lab/unavailable: true`，且集群无此标签节点。
  - `fact-f02a83eb46c2` (Metric) 确认 Pod 当前状态为 `Pending`，符合调度失败的预期结果。
  - 资源类事实排除资源不足因素。
- **结论：** 现有证据充分，根因为配置不匹配导致的调度失败，无证据不足情况。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.5s
├─ 并发证据采集: 33.6s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 33.6s (Evidence 27.2s, RCA 6.3s)
└─ 汇总总结: 14.8s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
