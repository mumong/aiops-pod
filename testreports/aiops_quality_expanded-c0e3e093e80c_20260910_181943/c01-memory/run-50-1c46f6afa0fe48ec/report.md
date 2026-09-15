## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod spec 中容器 app 配置了 1Pi 的 memory limit 和 requests，导致调度器判定所有 3 个节点 memory 不足（Insufficient memory），从而拒绝调度。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (fact-9f9975ca1210, fact-a28e361d367d) | `pod.status: Pending`, `pod.phase: Pending` | 确认 Pod 运行停滞于 Pending 状态 |
| 2 | K8s Config | kubernetes (fact-4e5741118bdc) | `container.resource_limit.memory: 1Pi` (容器 app) | 证实容器配置了 1Pi 内存上限 |
| 3 | K8s Config | kubernetes (fact-c3028d7160de) | `container.resource_request.memory: 1Pi` (容器 app) | 证实容器配置了 1Pi 内存请求 |
| 4 | K8s Event | kubernetes (fact-d5133ebcf9c5) | `FailedScheduling` (x14 over 71m): `0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..` | 调度器拒绝调度，3 个节点均内存不足 |
| 5 | K8s State | kubernetes (fact-d9815dfdc01b) | `PodScheduled` condition `False`, reason `Unschedulable` | 明确调度状态机进入 Unschedulable |
| 6 | Metric | prometheus (fact-5ceef38acfa4) | `kube_pod_status_phase` Pending 计数 1 (sample_count: 1) | 监控数据确认 Pod 处于 Pending 状态 |

**证据说明：**
K8s 配置（证据 2, 3）显示 Pod 申请了 `1Pi` 内存。K8s 事件（证据 4, 5）表明由于该资源需求过大，集群内全部 3 个节点均报告 `Insufficient memory` 且无法通过预占（preemption）解决，导致 `FailedScheduling`。状态和 Metric 数据（证据 1, 6）一致佐证了 Pod 长期处于 Pending 状态。日志和链路追踪因 Pod 未启动而缺失，不影响对该调度类故障的诊断。

## 🎯 根因分析 · g1

### 因果链

```text
容器资源请求异常 (memory limit/requests = 1Pi) → 调度器资源评估失败 (集群最大可用内存远小于 1Pi，判定 3 节点 Insufficient memory) → 调度动作失败 (FailedScheduling，Pod 保持 Unschedulable) → 现象 (Pod 处于 Pending 状态，nodeName 为 None)
```

### 根因结论

已确认根因：**Pod 规范（spec）中容器 `app` 的内存资源请求（request）和限制（limit）被错误配置为 `1Pi`，导致调度器判定集群中所有 3 个节点的资源均无法满足该需求。**

具体证据支持：
1.  **资源配置事实**：K8s 配置事实（fact-4e5741118bdc, fact-c3028d7160de）显示容器 `app` 的 `memory limit` 和 `memory request` 均为 `1Pi`。
2.  **调度失败机制**：K8s 事件事实（fact-d5133ebcf9c5）记录了 `FailedScheduling` 事件，明确指出 `0/3 nodes are available: 3 Insufficient memory` 且无可用预占受害者（No preemption victims）。
3.  **结果状态**：Pod 状态事实（fact-9f9975ca1210, fact-a28e361d367d）确认 Pod 处于 `Pending`，调度条件事实（fact-d9815dfdc01b）显示 `PodScheduled` 为 `False`。

上述证据链条完整，无逻辑断点，无需更多事实即可定性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 13.7s
├─ 并发证据采集: 40.2s
│  └─ g1 aiops-case-v02/workload: 40.2s (Evidence 33.5s, RCA 6.6s)
└─ 汇总总结: 13.1s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
