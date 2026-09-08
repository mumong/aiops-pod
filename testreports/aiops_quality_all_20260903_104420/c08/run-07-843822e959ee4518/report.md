## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | Pod workload-5c9c7b6489-fl85h 处于 CrashLoopBackOff 状态，表现为容器因内存超限被 OOMKilled 后频繁重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container last_terminated_reason: OOMKilled | 证实容器被内核 OOM 机制终止的直接状态 |
| 2 | K8s Event | Kubernetes | Warning BackOff restarting failed container app in pod workload-5c9c7b6489-fl85h (x63 over 21m) | 证实容器因 OOM 触发 BackOff 机制导致频繁重启 |
| 3 | K8s Config | Kubernetes | container.app resource_limit.memory: 64Mi | 提供导致 OOMKilled 的硬限制边界条件 |
| 4 | K8s Config | Kubernetes | container.app resource_request.memory: 24Mi | 确认内存配额极低，应用可用资源受限 |
| 5 | Metric | Prometheus | kube_pod_container_status_restarts_total: current 7, trend_evaluable=true (samples: 88) | 趋势证明重启行为持续发生，非单次故障 |
| 6 | Logging | Elasticsearch | pattern "memory allocation advanced" in 8 occurrences: allocated_mib first=10, last=48 | 证实应用内存使用量在短时间窗口内从 10Mi 增长至 48Mi |
| 7 | Tracing | Deepflow | HTTP GET /work response_code 200, occurrence_count 9, duration_us range 18163-102545 | 服务请求在处理期间（内存增长阶段）仍然成功响应，表明非阻塞性宕机 |
| 8 | K8s Config | Kubernetes | container.app exit_code: 137 | 配合 OOMKilled 状态码确认进程是被操作系统 OOM Killer 强制终止 |

**证据说明：**
1-4、8 组在 Kubernetes 维度确立了“低配容器被 OOMKilled 导致重启”的闭环状态。
6 提供了决定性的过程证据：日志中的内存分配增长（10Mi -> 48Mi）清晰展示了在 64Mi 硬限制逼近过程中的内存扩张行为。
7 补充了行为上下文，表明内存增长发生在正常的业务请求周期内，而非启动阶段，排除了冷启动问题。

## 🎯 根因分析 · g1

### 因果链
```text
容器应用存在内存泄漏（持续分配资源） → 内存使用量超过 64Mi 硬限制（limits.memory） → kubelet 触发 OOMKilled 终止容器（Exit Code 137） → 重启策略导致 CrashLoopBackOff（频繁重启）
```

### 根因结论
**已确认的根因：** 容器 `workload-5c9c7b6489-fl85h` 中的 `app` 容器存在内存泄漏。

应用在处理请求过程中，内存占用量呈现持续增长态势（日志证据：6 号）。在 21 分钟的观察窗口内，该容器经历了 7 次重启，且由于内存分配速度快且总量逼近硬限制（64Mi），最终导致 kubelet 触发 OOMKilled 机制终止进程（退出码 137），并进入 CrashLoopBackOff 状态。

现有证据已足以支撑该结论，决定性的事实包括 K8s OOMKilled 状态、明确的退出码 137、以及日志中展示的 10Mi 到 48Mi 的内存增长轨迹。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 22.1s
├─ 并发证据采集: 63.2s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 63.1s (Evidence 53.7s, RCA 9.3s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
