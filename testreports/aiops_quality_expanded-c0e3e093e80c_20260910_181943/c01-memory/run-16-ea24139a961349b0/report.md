## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload status Pending, scheduling failed due to Insufficient memory across all 3 nodes |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.condition` | `PodScheduled` 状态为 `False`，原因 `Unschedulable`，消息 `0/3 nodes are available: 3 Insufficient memory` | 确认调度失败的具体原因为节点内存不足 |
| 2 | K8s Config | `container.resource_request.memory` | 容器 `app` 请求了 `1Pi` 内存 (1,125,899,906,842,624 bytes) | 揭示了导致调度失败的异常资源需求 |
| 3 | K8s Config | `container.resource_limit.memory` | 容器 `app` 设置了 `1Pi` 内存硬限制 | 证实该 Pod 意图占用极不合理的巨大内存 |
| 4 | K8s Event | `event.message` | 调度器上报 `FailedScheduling`，记录显示过去 29 分钟内多次触发相同的内存不足告警 | 证明故障具有持续性和可复现性，非瞬时抖动 |
| 5 | Metric | `kube_pod_container_resource_requests` | 容器 `app` 的内存请求指标值为 `1125899906842624` 字节 | 从监控系统视角独立印证了 Pod 资源请求量的配置事实 |

**证据关联说明：**
事实 2 和事实 5 分别从 Kubernetes API 配置与 Prometheus 指标两个独立维度，一致确认了 Pod 配置了 `1Pi` 的内存请求。这一异常配置直接触发了事实 1 中的调度器状态变更与事实 4 中持续发生的事件告警，构成了完整的调度失败证据链。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 1Pi 内存请求与限制 → 调度器评估所有节点 allocatable memory 均无法满足该量级需求 → 触发 Insufficient memory 失败机制 → Pod 卡在 Pending 状态并持续被调度器拒绝
```

### 根因结论

已确认根因：**Pod 资源配置请求严重超出集群节点最大可用内存**。

集群中所有节点的最大可用内存（约 31Gi）远小于 Pod 请求的内存量（1Pi）。调度器在对所有 3 个节点进行评估时，均判定内存资源不足（Insufficient memory），且由于资源量级差距巨大，不可能存在可抢占的 Victim，导致 Pod 持续处于 `Pending` 状态且无法调度。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 41.8s
├─ 并发证据采集: 68.7s
│  └─ g1 aiops-case-v02/workload: 68.7s (Evidence 58.4s, RCA 10.3s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
