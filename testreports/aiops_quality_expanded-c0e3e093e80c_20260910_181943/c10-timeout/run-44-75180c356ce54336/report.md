## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | RecentRestart | Pod workload in CrashLoopBackOff due to Liveness Probe failures |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.last_terminated_reason: Error | 指示进程退出时的异常终止 |
| 2 | K8s State | kubernetes | container.waiting_reason: CrashLoopBackOff | 显示容器处于频繁重启后的暂停状态 |
| 3 | K8s State | kubernetes | pod.condition Ready: False (ContainersNotReady) | 容器不健康，未通过就绪检测 |
| 4 | K8s Event | kubernetes | Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded | 探针因响应超时被 Kubernetes 判定失败 |
| 5 | K8s Event | kubernetes | Back-off restarting failed container app | Kubelet 执行指数退避策略，拒绝立即重启 |
| 6 | K8s Config | kubernetes | container.resource_limit.memory: 64Mi | 提供硬性的内存上限值 |
| 7 | Logging | elasticsearch | GET /health HTTP/1.1 200 - (22:13:23 - 22:42:48 期间持续存在) | 证明应用进程本身仍在运行并响应健康检查 |
| 8 | Tracing | deepflow+tempo | L7 Flow: GET /health -> 200, duration: ~3001044us - 3001868us | 确认探针发起的请求已到达应用层，但应用层处理耗时超过 3 秒 |

**证据说明：**
Logging 和 Tracing 数据一致证明应用进程在异常发生前（约 22:13 至 22:42 区间）是存活的，且能够成功响应 `/health` 请求（返回 200）。这直接反驳了应用代码直接崩溃（Crash）的可能性，转而支持进程处于阻塞、死锁或极高负载状态。Tracing 中长达 3 秒以上的单次请求处理时长与 K8s Event 中 Liveness probe 的 `context deadline exceeded` 高度吻合，表明探针超时是因为应用层在处理请求时未能及时返回响应。

## 🎯 根因分析 · g1

```text
应用进程处理耗时过长（未确认触发 OOM 或 CPU 限制） → 应用层阻塞导致探针超时 → Liveness Probe 判定失败 → Kubelet 发送 SIGKILL 触发重启
```

**根因结论：**

**已确认的根因**是容器应用进程响应缓慢或阻塞，导致 Kubernetes 存活探针（Liveness Probe）判定失败并触发重启。
*   **现象支撑**：
    1.  **探针超时直接原因**：Tracing 数据显示在探针超时前的最近几次请求中，`/health` 端点响应耗时稳定在 3000ms 以上（见证据 #8），超过了探针的超时阈值。
    2.  **排除直接崩溃**：Logging 和 Tracing 表明，在容器终止前（见证据 #7），应用进程依然能够处理 HTTP 请求并返回 200 状态码，并未出现直接的 Crash 或 OOM Kill 迹象。
    3.  **重启循环机制**：K8s 检测到 Probe 失败后尝试重启，但应用进程可能仍处于阻塞或高负载状态，导致再次启动后再次无法在超时阈值内响应，从而陷入 `CrashLoopBackOff`（见证据 #2, #3）。

**未确认的环节**：
*   输入中的 `formal_rca` 假设根因为 `OOM Killer`（Exit Code 137），但目前的证据（特别是应用进程能持续响应 200 的请求日志）并不支持 OOM 是此次 **特定** 探针超时事件的直接触发原因。Exit Code 137 通常指被 SIGKILL，若由 OOM 触发，通常意味着进程瞬间被杀；而 Tracing 记录的长耗时请求表明进程是“假死”或极度缓慢。若 Exit Code 137 确实存在，则表明在探针失败后的某次重启中，进程可能再次发生了被强制终止的情况。
*   **结论修正**：当前证据更支持“应用进程无响应/阻塞导致探针超时”作为直接故障链；OOM 或资源耗尽仅为可能的潜在诱发因素或后续重启中再次发生的行为，需更多内存指标（`trend_evaluable=true` 的 Prometheus 数据）验证。当前根因为：**Liveness Probe 因应用处理延迟超时，触发容器重启循环。**

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 18.7s
├─ 并发证据采集: 90.5s
│  └─ g1 aiops-case-v17/workload: 90.5s (Evidence 83.0s, RCA 7.4s)
└─ 汇总总结: 15.2s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
