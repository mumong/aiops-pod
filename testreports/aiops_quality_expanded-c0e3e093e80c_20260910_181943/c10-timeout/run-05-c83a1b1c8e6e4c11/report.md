## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | {'container': 'app', 'message': 'back-off 5m0s restarting failed container=app pod=workload_aiops-case-v17(85aece07-6ffa-41db-9e5a-f351771a8864)'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | exit_code: 137, reason: Error | 确认容器异常终止，137 号信号通常指示进程被 OOMKiller 终止 |
| 2 | K8s Config | kubernetes | memory_limit: 64Mi, memory_request: 8Mi | 容器存在极低的内存硬限制，符合导致 137 号退出的资源瓶颈特征 |
| 3 | Metric | prometheus | kube_pod_container_status_restarts_total: 7 (label: container=app) | 确认容器发生了多次重启，与 K8s 状态中的 restart_count 一致 |
| 4 | K8s State | kubernetes | container.waiting_reason: CrashLoopBackOff, message: back-off 5m0s restarting failed | 确认系统因频繁失败正在执行指数退避重启 |
| 5 | Logging | elasticsearch | listening on 18080 | 确认容器启动时服务监听正常，排除进程启动阶段立即崩溃 (Exit 0/1) 的可能性 |
| 6 | Tracing | deepflow | L7 GET /health (200), duration 3001057.0~3001920.0us (11 occurrences) | 证明在观察窗口内服务具备正常响应能力，非网络/配置连接失败 |

**证据互证说明**：
退出码 137 (事实#1) 与极低内存限制 64Mi (事实#2) 高度吻合，指向内存超限被系统强制杀死的机制。虽然容器经历了多次重启 (事实#3, #4)，但日志 (事实#5) 与流量 (事实#6) 显示当前服务处于健康可用状态，证明之前的 CrashLoopBackOff 状态是由突发性的资源耗尽导致，且该状态在当前快照中已自愈或暂停，缺失了触发第一次 Crash 的具体时刻的日志证据。

## 🎯 根因分析 · g1

```text
异常根因：容器资源限制过低引发 OOMKilled (推测) → 机制：内存超限触发内核 Kill 信号 → 直接失败：exit_code 137 与 CrashLoopBackOff → 用户现象：当前 pod 状态异常，但近期流量健康
```

**根因结论**：

**证据不足**。

虽然事实 #1 (exit_code 137) 和事实 #2 (64Mi 内存限制) 强烈暗示根因为 OOM (Out Of Memory)，导致容器频繁退出 (事实 #3, #4)，但缺乏在首次异常发生时间窗口的具体日志或监控证据来证实内存指标在崩溃前确实达到了 64Mi 上限。当前状态显示服务已恢复健康 (事实 #5, #6)，且诊断状态为 `inconclusive`。缺少能够直接关联“第一次 Crash”瞬间资源利用率的决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 26.0s
├─ 并发证据采集: 95.2s
│  └─ g1 aiops-case-v17/workload: 95.2s (Evidence 84.3s, RCA 10.7s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
