## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 处于 Pending 状态，持续被调度器拒绝 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `FailedScheduling ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 明确指出调度失败原因是节点亲和性/选择器不匹配 |
| 2 | K8s Config | `container.resource_request.cpu` | `5m` | 排除 CPU 资源不足导致的调度延迟 |
| 3 | K8s Config | `container.resource_request.memory` | `8Mi` | 排除内存资源不足导致的调度延迟 |
| 4 | K8s State | `pod.phase` | `Pending` | 确认 Pod 未分配到节点，处于等待状态 |
| 5 | K8s State | `pod.condition` | `PodScheduled=False; Reason=Unschedulable` | 证实调度器已评估但未能找到满足条件的节点 |
| 6 | K8s Config | `node_selector` | `aiops.lab/unavailable: 'true'` | 提供导致不匹配的具体配置原因 |
| 7 | Metric | `kube_pod_status_phase` | `Pending=1` | 确认当前阶段为 Pending，且无 `Failed` 状态（`Failed=0`） |

**证据说明：**
- Kubernetes 状态（证据 4, 5）与事件（证据 1）相互印证，均指向调度器无法找到匹配节点。
- K8s 配置（证据 2, 3, 6）表明资源请求量极低，排除了资源瓶颈；根本原因确认为标签 `aiops.lab/unavailable: 'true'` 的要求与集群实际节点状态不符。
- 指标（证据 7）从侧面验证了 Pod 持续处于 Pending 状态且未进入其他失败状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义了 nodeSelector {aiops.lab/unavailable: 'true'} → 调度器遍历 3 个节点均因选择器不匹配而过滤 → 默认调度器返回 Unschedulable，Preemption 无效 → Pod 状态保持 Pending
```

### 根因结论

- **已确认的根因**：Pod `workload-68c557d875-llhkh` 配置了节点选择器 `nodeSelector {aiops.lab/unavailable: 'true'}`，但集群内当前 3 个节点均未设置该标签。这导致调度器在遍历所有可用节点时均因节点亲和性/选择器不匹配而拒绝调度，且该问题无法通过抢占（Preemption）解决。相关证据：证据 1、证据 6。

- **证据完整性说明**：现有证据足以确认当前异常的直接原因。未确认项包括“集群中是否存在其他未纳入本次评估的具有该标签的节点”，但基于当前事实，Pod 的调度失败已明确归因于标签配置与实际节点状态的不匹配。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 30.4s
├─ 并发证据采集: 51.1s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 51.1s (Evidence 41.0s, RCA 9.9s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- 未调用 Runbook
