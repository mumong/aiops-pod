## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason: OOMKilled`, `container.last_exit_code: 137` | 核心证据，直接确认进程因内存超限被终止 |
| 2 | K8s State | kubernetes | `pod.status: Running`, `container.restart_count: 22` | 症状记录，显示容器虽然状态为 Running，但已崩溃重启 22 次 |
| 3 | K8s Config | kubernetes | `resource_limit.memory: 64Mi` | 上下文约束，确立了触发 OOM 的硬限制边界 |
| 4 | Logging | elasticsearch | `pattern: memory allocation advanced`, `numeric_fields: allocated_mib first=12, last=48` (窗口: `18:13:55` - `18:14:31`) | 现象描述，记录单次请求处理期间内存使用量快速从 12MB 攀升至 48MB，逼近且可能突破 64Mi 限制 |
| 5 | Tracing | deepflow | `l7_flow: GET /work, response_code: 200, duration_us: 7749-20985` | 关联上下文，确认触发内存分配的对应请求路径、状态及耗时情况 |

**证据印证说明：**
1. K8s 的 `OOMKilled` (E1) 与 `Exit Code 137` (E1) 直接解释了为何容器频繁重启 (E2)。
2. 日志 (E4) 中内存使用量的急剧上升，为 K8s 的 OOM 判定提供了直接的应用层行为解释，证明内存消耗发生在业务请求处理过程中。
3. 追踪记录 (E5) 提供了触发该内存消耗的具体网络调用上下文（GET /work）。

## 🎯 根因分析 · g1

### 因果链

```text
Memory limit (64Mi) too low for application working set → Container memory usage exceeds limit during request processing → Kubernetes OOMKills container (Exit Code 137) → Pod enters CrashLoopBackOff due to repeated restarts
```

### 根因结论

已确认的根因为容器 `app` 在处理请求时的内存工作集超过了其 64Mi 的硬限制。
Kubernetes 内核在内存超限后强制终止容器并返回 Exit Code 137（证据 #1），这直接导致了 Pod 的 CrashLoopBackOff 状态及 22 次重启现象（证据 #2）。日志数据（证据 #4）证实了内存分配与业务请求之间的直接关联，进一步排除了后台进程或系统负载的干扰。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 26.0s
├─ 并发证据采集: 59.1s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 59.1s (Evidence 49.9s, RCA 9.1s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
