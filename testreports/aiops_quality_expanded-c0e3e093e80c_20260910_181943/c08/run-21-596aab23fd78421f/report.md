## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | Pod workload-5c9c7b6489-p8462 处于 CrashLoopBackOff 状态（重启16次，BackOff事件持续68分钟），最近一次终止原因为 OOMKilled |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 31s (x259 over 68m) kubelet  Back-off restarting failed container app in pod workload-5c9c7b6489-p8462...` | 确认 Pod 进入 CrashLoopBackOff 且已持续 68 分钟。 |
| 2 | K8s State | Kubernetes | `Exit Code: 137`, `Reason: OOMKilled` | 确认容器是被操作系统内存不足杀手强制终止，而非应用逻辑错误。 |
| 3 | K8s Config | Kubernetes | `resource_limit.memory`: `64Mi`, `resource_request.memory`: `24Mi` | 提供容器运行的硬资源边界证据。 |
| 4 | Logging | Elasticsearch | `allocated_mib`: `first=10`, `last=48` (处理路径 `/work`, `http_status: 200`) | 记录在应用返回 HTTP 200 的正常请求中，内存分配量从 10MiB 增至 48MiB，证明内存持续增长。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason`: `OOMKilled` (sample=1) | 独立监控数据佐证了 OOM 终止状态。 |
| 6 | Tracing | Deepflow | `HTTP GET /work` → `response_code: 200` (9 occurrences, 2026-09-11 07:04:01~41) | 网络层面确认在崩溃发生前后，应用层面对 `/work` 路由的响应是正常的，问题发生在请求处理后的资源回收或累积阶段。 |

**证据印证说明**：
日志证据（编号 4）与追踪证据（编号 6）共同证实 `/work` 请求在业务逻辑上是成功的（HTTP 200），但伴随显著的内存分配增长。这一消耗直接导致容器触发了 K8s 配置的硬性限制（编号 3），进而引发内核 OOMKilled（编号 2），最终形成持续的重启循环（编号 1, 5）。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存 Limit (64Mi) 限制 → 业务请求 /work 内存分配持续增长 (10Mi→48Mi) → 突破 Limit 触发 OOM Killer (Exit 137) → Kubelet 重启并进入 CrashLoopBackOff (68m)
```

### 根因结论

已确认根因为：**容器 `app` 配置的内存上限 (64Mi) 低于业务处理 `/work` 请求所需的实际峰值内存，导致内存耗尽被 OOM Killer 强制终止。**

支持事实：
- 容器运行硬性限制为 64Mi（证据 #3）；
- 日志记录显示在成功处理的请求中，内存分配量已高达 48Mi 且呈现增长趋势（证据 #4）；
- 容器退出码 137 及 OOMKilled 事件证实了内核层面的内存杀杀行为（证据 #2, #5）；
- 网络流量确认崩溃发生在正常响应的请求处理后（证据 #6）。

缺失事实：
- 仅能确认内存持续消耗导致 OOM，但无法通过现有日志区分是代码层面的**内存泄漏**（如缓存未释放）还是**单次请求处理过程中的瞬时高负载**（需压测或分析内存碎片分布来区分）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 21.8s
├─ 并发证据采集: 46.8s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 46.8s (Evidence 34.7s, RCA 11.9s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
