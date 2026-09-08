## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | RecentRestart | Pod aiops-case-10/workload-79d9f8fd88-bwqhh 处于 CrashLoopBackOff 状态，Container app 反复崩溃重启（重启13次），退出码 137，且伴随 Liveness Probe 失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.resource_limit.memory` | `96Mi` | 设定了内存硬限制，为 OOM 触发提供阈值依据。 |
| 2 | K8s State | `container.last_exit_code` | `137` | 直接表明容器被 OOM Killer 强杀，是核心故障特征。 |
| 3 | K8s State | `pod.status` | `Running` (Reason: CrashLoopBackOff, Exit Code: 137) | 确认可见现象为反复重启导致的崩溃循环。 |
| 4 | K8s Event | `Kubelet Liveness` | `Liveness probe failed: HTTP probe failed with statuscode: 500` | 证明重启后资源紧张导致探针超时或拒绝服务。 |
| 5 | K8s Event | `Kubelet BackOff` | `Back-off restarting failed container app... (x98 over 25m)` | 确认 Kubernetes 正在执行指数退避的重启机制。 |
| 6 | Metric | `kube_pod_container_status_restarts_total` | 从 1 跃升至 13 (sample_count: 31, trend_evaluable: true) | 持续且快速的重启趋势，印证 CrashLoopBackOff 的持续性。 |

**证据印证说明：**
事实 #2 (Exit Code 137) 与事实 #1 (96Mi Limit) 形成了“资源超限引发强杀”的闭环逻辑。事实 #3 和 #5 展示了该机制导致的直接结果（重启循环），而事实 #4 表明在重启间隙，由于内存占用可能再次激增，导致 Liveness 探针无法正常响应（返回 500），从而加速了下一轮重启。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存持续增长突破 96Mi 限制 (事实1) → OOM Killer 强制终止进程 (Exit 137, 事实2) → 容器重启后资源/响应再次恶化触发 Liveness 失败 (事实4) → Kubernetes 进入 CrashLoopBackOff (事实3, 5)
```

### 根因结论

**已确认的根因**：容器 `app` 内存使用量超过了硬限制 `96Mi`（证据 #1），触发 Linux OOM Killer 机制将进程终止（证据 #2，Exit Code 137）。容器重启后，由于内存消耗过快或资源紧张，导致应用无法在限期内响应健康检查，Liveness 探针超时并返回 500 错误（证据 #4），进而导致 Kubernetes 持续重启并进入 CrashLoopBackOff 状态（证据 #3, #5）。

**证据不足说明**：缺乏 `container_memory_working_set_bytes` 的具体时序数据，因此无法精确描绘内存突破 96Mi 的上升斜率，暂时无法区分是内存泄漏（Memory Leak）还是突发负载导致的资源争抢。

---

## 📊 性能统计

```text
├─ 总耗时: 3.0m
├─ 问题定位: 21.7s
├─ 并发证据采集: 150.6s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 150.6s (Evidence 137.3s, RCA 13.1s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
