## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod workload in aiops-case-v02 remains in Pending state with FailedScheduling events. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | default-scheduler | `FailedScheduling ... 0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found` | 提供调度失败的直接原因与集群节点内存不足的现状 |
| 2 | K8s Config | Pod 配置 | `container.resource_request.memory: 1Pi` | 展示导致调度失败的请求量，数值超出物理内存量级 |
| 3 | K8s State | Pod 状态 | `pod.status: Pending`, `pod.condition(PodScheduled): False` | 确认故障持续且未发生自愈或转态 |
| 4 | Metric | Prometheus | `kube_pod_container_resource_requests(container=app, resource=memory): 1125899906842624 bytes` | 独立验证内存请求值为 `1Pi` (1125899906842624 字节) |

**证据说明**：
- **K8s Event (事实1)** 与 **Metric (事实4)** 形成闭环：调度器报告“内存不足”，Prometheus 数据精确量化该内存请求为 `1PiB`，排除了网络、磁盘或其他资源导致的偶发性调度失败。
- **K8s Config (事实2)** 与 **K8s Event (事实1)** 建立因果链：正是由于配置了物理集群不可达的内存请求值，导致了调度器在 3 个节点上均无法找到符合要求的资源并返回 Insufficient memory。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 资源配置 memory_request=1PiB → 调度器遍历节点发现最大可用内存远低于请求量 → 内存资源校验失败且无抢占对象 → Pod 持续 Pending
```

### 根因结论

**根因已确认：Pod 资源清单中内存请求配置异常（`1PiB`）。**

Pod `aiops-case-v02/workload` 的 `container.resource_request.memory` 被设置为 `1Pi`。集群所有节点的最大可用内存均远低于此值（根据事件日志推断，最大节点可用内存约 32.75 GiB）。这一数值配置导致调度器无法在集群中寻址到满足条件的节点，从而抛出 `FailedScheduling` 事件。Metric 数据 `1125899906842624 bytes` 进一步从观测侧证实了该异常数值。

**未知项**：目前证据仅能证明配置存在且不合理，无法判断 `1PiB` 是 Manifest 中的拼写错误还是刻意的错误配置。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 14.5s
├─ 并发证据采集: 57.4s
│  └─ g1 aiops-case-v02/workload: 57.4s (Evidence 48.6s, RCA 8.7s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- 未调用 Runbook
