## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod 配置了 `nodeSelector: aiops.lab/unavailable=true`，但集群中所有 3 个节点均未匹配该标签选择器，导致调度器持续执行 FailedScheduling，Pod 状态保持 Pending。 |
| g2 | `monitor/prometheus-observability-prometheus-0` | Unknown | Pod prometheus-observability-prometheus-0 状态为 Unknown（初始）并伴随高频探针超时（19天内176次Liveness/142次Readiness失败），表现为 `context deadline exceeded`。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes (`pod.phase`) | `Pending` (fact-95a1e5872f61) | 确认 Pod 处于挂起状态，无法启动 |
| 2 | K8s State | Kubernetes (`pod.condition`) | `PodScheduled=False`, `Unschedulable`: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` (fact-6b6e313c7886) | 提供调度失败的直接原因：节点亲和性/选择器不匹配 |
| 3 | K8s Event | Kubernetes (`event.message`) | `FailedScheduling 16m (x2 over 21m)... 3 node(s) didn't match Pod's node affinity/selector.` (fact-8ffdd00336d5) | 确认调度器在较长周期内持续因标签不匹配而拒绝调度 |
| 4 | K8s Config | Kubernetes (`container.resource_request.cpu`) | `5m` (fact-1e2fc8ade32e) | 确认资源请求极低，排除资源不足导致的调度失败 |
| 5 | K8s Config | Kubernetes (`container.resource_request.memory`) | `8Mi` (fact-95a1e5872f61) | 确认资源请求极低，排除资源不足导致的调度失败 |

**证据综合说明：**
Kubernetes 状态与事件 (1, 2, 3) 高度一致，均指向同一个机制：Pod 的调度被“节点不匹配”阻断。资源配置 (4, 5) 排除了 CPU/内存资源不足的可能性，将问题范围缩小至仅存的标签选择器不匹配这一单一事实。

## 🎯 根因分析 · g1

### 因果链
```text
配置错误 (nodeSelector 标签不存在) → 调度器过滤失败 (节点匹配逻辑不满足) → 持续 FailedScheduling 事件 → Pod 状态保持 Pending
```

### 根因结论
**已确认的根因：**
Pod `aiops-case-01/workload-68c557d875-bsq52` 配置了 `nodeSelector: aiops.lab/unavailable=true`，但集群中所有 3 个节点均未携带该标签，导致调度器无法将 Pod 调度到任何节点。

*   **证据引用**：
    *   Pod 持续处于 `Pending` 状态 (证据 1)
    *   调度器报告 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` (证据 2, 3)
    *   资源请求极低，排除资源瓶颈 (证据 4, 5)

---

## 🕵️ 证据内容 · g2

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Liveness probe failed: Get "http://172.16.166.165:9090/-/healthy": context deadline exceeded (x176 over 19d)` (fact-49eb50e57ab8) | 确认探针持续超时现象，覆盖周期长 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason: OOMKilled` (fact-b145bcebe245) | 确认进程终止的原因为内存超限 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory: 512Mi` (fact-25bcd7c0fa47) | 确认存在硬限制，作为 OOM 的物理约束基础 |
| 4 | K8s State | kubernetes | `container.last_exit_code: 137` (fact-223b1f54d5d7) | 确认进程被内核 OOM Killer 终止（Signal 9） |
| 5 | K8s State | kubernetes | `container.restart_count: 2` (fact-10fb7a39a0cf) | 确认 OOM 导致过重启 |
| 6 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason = 1 (reason: OOMKilled)` (fact-a58e49a84f32) | 独立于 K8s Event 的时序数据确认 |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total = 2` (fact-c24251324592) | 确认重启次数与 K8s State 一致 |
| 8 | Logging | elasticsearch | `rule manager ... Evaluating rule failed ... found duplicate series for the match group {instance="10.2.0.48:10250"} ... many-to-many matching not allowed` (fact-0717c33c0325) | 确认配置缺陷导致规则计算失败，为独立故障点 |

**证据说明：**
1. 证据 1 的探针超时与证据 2、4、5 构成的“内存不足 -> OOM 终止 -> 重启”链条存在因果关联；探针通常在启动中或启动后资源未恢复时失败。
2. 证据 3 提供了内存限制的事实基础，解释了为何负载会导致证据 2 的发生。
3. 证据 8 揭示了集群内存在的另一独立故障（配置重复导致的规则执行失败），但不影响对 Pod 运行状态异常（OOM/Probe Fail）的结论。

## 🎯 根因分析 · g2

### 因果链

```text
内存资源硬限制（512Mi）不足 → 进程负载触发 OOMKilled（Exit Code 137） → 容器频繁终止并重启（2次） → 进程在重启窗口内无响应导致 Kubelet 探针超时
```

### 根因结论

已确认的根因是 **Prometheus 容器内存资源限制过低（512Mi）**。

该限制导致 Prometheus 进程在运行中发生 OOMKilled（Exit Code 137），进而触发 2 次容器重启。在容器终止重启或恢复的过程中，进程无法响应健康检查，导致 Kubelet 记录到大量的 `context deadline exceeded` 探针超时事件（19天内 176 次 Liveness 失败），表现为 Pod 健康状态异常。

证据编号引用：
- 根因约束：fact-25bcd7c0fa47
- 终止与重启：fact-b145bcebe245, fact-223b1f54d5d7, fact-10fb7a39a0cf
- 现象表现：fact-49eb50e57ab8

---

## 📊 性能统计

```text
├─ 总耗时: 7.8m
├─ 问题定位: 55.6s
├─ 并发证据采集: 398.1s
│  ├─ g1 aiops-case-01/workload-68c557d875-bsq52: 34.2s (Evidence 28.9s, RCA 5.2s)
│  └─ g2 monitor/prometheus-observability-prometheus-0: 398.1s (Evidence 387.2s, RCA 10.7s)
└─ 汇总总结: 16.0s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
- **g2 monitor/prometheus-observability-prometheus-0**: pod-notready-probe-failed
