## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Pod workload-79d9f8fd88-sbqvc处于CrashLoopBackOff状态，容器反复重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.waiting_reason: CrashLoopBackOff; last_terminated_reason: Error; last_exit_code: 137 | 确认 Pod 处于因非零退出码频繁重启的状态 |
| 2 | K8s Event | kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 (10m, x17) | 确认为 kubelet 主动触发杀进程的直接原因 |
| 3 | Logging | elasticsearch | 工作负载路径 `/work` 持续返回 `http_status: 200` (7次, 04:09-04:32) | 证明应用业务逻辑在处理请求时功能正常，排除应用整体宕机 |
| 4 | Tracing | deepflow | `GET /work` 流量 7 次，响应码 200，关联 trace_ids (如 `b877...`) 与日志时间窗一致 | 独立网络观测确认业务流量在探测失败期间仍可成功处理 |
| 5 | Metric | prometheus | `container_memory_working_set_bytes` max 15.5 MiB (3641344.0 -> 15466496.0); limits: 96Mi | 排除 OOMKill (Exit 137 通常关联 OOM，但此处内存远低于限制) |

日志中的工作负载路径（/work）与 Tracing 中的 `/work` 流量存在明确关联，两者时间窗（04:09-04:32）高度重合，证实业务功能在线。内存监控数据（Fact 5）显示峰值仅约 15 MiB，远低于 96 MiB 的硬限制，且未出现 OOM Kill 的典型特征，结合 Kubernetes 事实中明确的 `Exit Code: 137` 与 `Liveness probe failed` 事件的时间序列，可确认该退出码由 Liveness Probe 判定失败触发的强制终止导致，而非系统级资源耗尽。

## 🎯 根因分析 · g1

### 因果链

```text
应用健康检查端点（/health）返回 HTTP 500 → kubelet 判定 Liveness Probe 失败并执行 Killing 操作 → 容器进程被强制终止 (Exit Code 137) → Pod 陷入 CrashLoopBackOff 循环
```

### 根因结论

已确认的根因是 **应用 Liveness Probe 配置或实现异常**，导致 kubelet 持续收到 500 响应并杀死容器。证据包括：
- **K8s 事件与状态** (Fact 1, 2) 直接记录探针 500 错误及随后的容器重启事件链。
- **应用健康证明** (Fact 3, 4) 显示业务路径 `/work` 在相同时间段内正常响应 200，证明应用自身未崩溃，排除整体服务不可用。
- **排除资源异常** (Fact 5) 显示内存使用远低于限制，排除了 OOM 导致 137 退出的可能。

**缺失事实**：无法确认 `/health` 返回 500 的具体代码级原因（如依赖缺失或逻辑错误），以及为何 `/health` 与 `/work` 行为不一致。

---

## 📊 性能统计

```text
├─ 总耗时: 3.8m
├─ 问题定位: 21.8s
├─ 并发证据采集: 193.1s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 193.1s (Evidence 178.3s, RCA 14.6s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
