## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod `aiops-case-v02/workload` 的 Container `app` 配置了极大的内存限制 `Limits.memory=1Pi`。受 `LimitRanger` 等 admission controller 影响，该限制被填充为对应的资源请求 `Requests.memory=1Pi`。该请求量远超集群 3 个节点的所有可用资源总和，且因资源需求过大，系统无法找到任何可抢占的 Pod（No preemption victims found），导致调度器持续报告 `Insufficient memory` 异常，使 Pod 保持在 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | `execute_pod_config` | `container.app.resource_limit.memory: 1Pi` | 异常触发源；配置了不可行的超大量级内存限制。 |
| 2 | K8s Config | `execute_pod_config` | `container.app.resource_request.memory: 1Pi` | 机制验证：LimitRanger 将上述 limit 填充为 request，导致调度器必须寻找 1Pi 的可用资源。 |
| 3 | K8s Event | `execute_pod_events` | `FailedScheduling: 0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found...` | 直接现象：调度器在所有节点内存不足且无抢占目标，判定无法调度。 |
| 4 | K8s State | `execute_pod_config` | `pod.status: Pending` | 当前系统状态，Pod 未能被分配节点。 |
| 5 | Metric | `execute_pod_promql` | `kube_pod_status_phase {phase="Pending", container="kube-state-metrics"} = 1` | 独立指标验证：集群中存在处于 Pending 状态的 Pod 实例，确认异常持续。 |

**证据印证说明：**
K8s 配置显示 Pod 内存 Request 高达 1Pi（证据 #1, #2），这从逻辑上解释了为何调度器在所有 3 个节点均报告 Insufficient memory（证据 #3）。调度器同时确认无符合条件的 Pod 可被抢占，使得“内存不足”成为硬性阻碍。状态（#4）与独立指标（#5）证实了该异常并非瞬时波动，而是因配置缺陷导致的持续性调度失败。

## 🎯 根因分析 · g1

### 因果链

```text
Container 配置 Limits.memory=1Pi → Admission Controller 填充 Requests.memory=1Pi → 节点可用内存不足且无 Preemption 对象 → Pod 持续 Pending
```

### 根因结论

已确认根因为 **Pod 资源配置极度不合理**。

具体而言，Pod `aiops-case-v02/workload` 的 Container `app` 被配置了 `1Pi`（Pebibyte）的内存限制。Kubernetes 的 `LimitRanger` Admission Controller 将其直接填充为等量的资源请求。由于集群所有节点的总可用内存远小于 1Pi，且不存在任何符合资源抢占条件（preemption）的 Pod，Scheduler 在三次尝试后均判定 `Insufficient memory` 并拒绝调度。

决定性证据为：
- **Fact #1, #2**：证实了 1Pi 的请求量级超出了物理集群承载能力。
- **Fact #3**：直接反映了调度器基于该资源缺口给出的最终判定（Insufficient memory, No preemption victims）。

---

## 📊 性能统计

```text
├─ 总耗时: 56.7s
├─ 问题定位: 15.4s
├─ 并发证据采集: 32.0s
│  └─ g1 aiops-case-v02/workload: 32.0s (Evidence 24.8s, RCA 7.1s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
