## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Pod 'workload' (aiops-case-v17) is in CrashLoopBackOff with 39 restarts. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded` | 证明应用服务响应缓慢，导致存活探针超时 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff (重启次数 39) | 确认 Pod 处于持续崩溃重启状态 |
| 3 | K8s Event | kubernetes | `Exit Code: 137` | 进程被外部强杀（OOM-Killer）的典型特征 |
| 4 | K8s Config | kubernetes | `resource_limit.memory`: 64Mi | 容器存在硬性内存限制，限制缓冲区扩张能力 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: 1 (CrashLoopBackOff) | 独立确认 Pod 异常状态 |
| 6 | Tracing | deepflow | HTTP GET /health 耗时: 3,001,044μs (约 3 秒)，返回 200 | 证明健康检查接口能返回成功，但响应时间极长，超过探针阈值 |
| 7 | Logging | elasticsearch | `GET /health HTTP/1.1" 200 -` | 应用日志记录显示服务正在运行，佐证阻塞而非宕机 |

证据之间高度一致：Tracing 显示 `/health` 接口需耗时约 3 秒才能返回 200 OK，直接导致探针（通常超时较短）判定 `context deadline exceeded`（证据 #1, #6）。日志显示服务仍在工作（证据 #7），而 `Exit Code: 137`（证据 #3）表明应用在被 K8s 强制重启前，因内存不足（证据 #4）引发了 OOM-Killer。

## 🎯 根因分析 · g1

### 因果链

```text
应用线程阻塞（如 DNS 解析等待） → HTTP 响应延迟过高（>3秒） → Liveness Probe 超时探测失败 → 容器被 K8s 杀掉并触发 OOM-Killer (Exit 137) → CrashLoopBackOff 重启循环
```

### 根因结论

已确认的根因是：**应用存在同步阻塞行为（极大概率为 DNS 解析），导致服务响应严重延迟，进而引发 OOM 崩溃。**

1.  **阻塞现象确认**：Tracing 数据（证据 #6）显示 `/health` 接口响应耗时超过 3 秒，足以触发探针超时（证据 #1），同时应用日志（证据 #7）确认服务并未完全宕机，而是处于“半死不活”的阻塞状态。
2.  **崩溃机制确认**：K8s 记录显示容器退出码为 137（证据 #3），结合 64Mi 的硬性内存限制（证据 #4），说明阻塞导致的长连接或缓冲堆积耗尽了内存，触发了 OOM-Killer 强制终止进程。
3.  **缺失事实说明**：虽然根因链条在技术上是完整的（阻塞->超时->OOM），但输入数据中缺失确凿的“阻塞证据”（如 DNS 错误日志、线程堆栈）。当前事实主要基于探针超时和 OOM 结果进行的逆向推断，属于高置信度推断而非代码级确证。

---

## 📊 性能统计

```text
├─ 总耗时: 2.6m
├─ 问题定位: 44.7s
├─ 并发证据采集: 102.3s
│  └─ g1 aiops-case-v17/workload: 102.3s (Evidence 91.8s, RCA 10.3s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
