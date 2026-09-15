## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 处于 Pending 状态，无法调度至任何节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | `PodScheduled=False`: 0/3 nodes available: 3 Insufficient memory. preemption: 0/3 nodes available: 3 No preemption victims found | 确认 Pod 因内存不足被调度器拒绝，且无抢占对象 |
| 2 | K8s Config | container.resource_request.memory | `1Pi` (app) | 提供调度失败的直接原因：请求量级远超常规集群节点容量 |
| 3 | K8s Config | container.resource_limit.memory | `1Pi` (app) | 进一步确认该极端内存需求为显式配置而非默认推断 |
| 4 | K8s Event | event.message | `FailedScheduling`: 13m (x2 over 18m) 3 Insufficient memory | 验证故障在 18 分钟内持续存在，确认为系统性阻塞 |

上述 Kubernetes 状态与事件事实相互印证：Pod 因 Request 高达 1Pi 的内存导致调度器在全部 3 个节点上均评估失败，且由于无其他 Pod 可抢占，故障持续阻塞。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 配置了 1Pi memory limit/request → 调度器评估所有节点内存不足以支持该 Limit → 调度器拒绝调度并抛出 FailedScheduling 事件 → Pod 持续处于 Pending 状态
```

### 根因结论

已确认根因是 Pod `aiops-case-v02/workload` 配置了 `1Pi` 的内存资源请求/限制（证据 #2, #3）。该配置导致 Kubernetes 调度器在评估所有 3 个可用节点时，发现内存资源严重不足（`Insufficient memory`），且集群内无其他资源占用可被抢占以腾挪空间（证据 #1, #4），从而致使 Pod 无法调度并持续处于 Pending 状态。

**未确认事项**：
- 集群各节点具体的 Allocatable Memory 数值（虽足以推断节点无法承载 1Pi，但具体数值缺失）。
- 该 `1Pi` 配置是否为故意的大数据作业配置或配置失误（需结合业务上下文，但非当前调度故障的直接技术根因）。

---

## 📊 性能统计

```text
├─ 总耗时: 52.4s
├─ 问题定位: 12.3s
├─ 并发证据采集: 32.4s
│  └─ g1 aiops-case-v02/workload: 32.4s (Evidence 25.3s, RCA 7.0s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
