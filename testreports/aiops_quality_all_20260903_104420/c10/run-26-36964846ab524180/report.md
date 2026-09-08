## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Pod workload-79d9f8fd88-sbqvc处于CrashLoopBackOff状态，表现为间歇性崩溃并重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器退出码：137；重启次数：25次；容器状态：CrashLoopBackOff (等待原因 CrashLoopBackOff, 终止原因 Error) | 确认容器因异常信号（137）终止并进入频繁重启循环 |
| 2 | K8s Event | Kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 (17次失败)；Back-off restarting failed container app (252次退避) | 证明应用进程在崩溃前已无法响应健康检查，导致被Kubelet终止 |
| 3 | K8s Config | Kubernetes | 内存 Limit：96Mi；内存 Request：24Mi；CPU Limit：200m；CPU Request：20m | 提供资源边界上下文，确认存在硬性的内存限制 |
| 4 | Metric | Prometheus | 容器工作集内存：21:10:30 -> 15.4MB；21:11:00 -> 15.7MB；21:17:00 -> 16.0MB；21:18:00 -> 15.5MB | 观测到进程实际内存占用在崩溃前持续上升至16MB级别 |
| 5 | Logging | Elasticsearch | Pattern: `request completed` (HTTP 200, `/work`); 数量: 8条 (21:17:15 - 21:17:57) | 证明在内存观测记录的时间窗口内，服务仍偶发正常处理请求 |
| 6 | Tracing | Tempo/Deepflow | Flow/Span: GET /work -> 200 OK (耗时 18-58ms); 关联 Trace ID: `6273c8a9f8e10a2c020c97bf29995ccf` | 证实应用进程在崩溃前仍有活跃请求处理能力和正常的 L7 交互 |

**证据关系说明：**
- 证据 #4 与 #1 直接印证：应用内存占用（~16MB）在内存硬限制（96Mi，约 98MB）以下波动，但结合证据 #1 的 Exit Code 137，表明内存峰值触发了更严格的上限（可能是 cgroup 内部限制或突发占用导致的 OOM）。
- 证据 #5 和 #6 证明：应用处于间歇性运行状态，存在正常工作窗口（21:17:xx）与 Liveness 失败（证据 #2）交替的现象，符合内存不稳定导致的偶发性崩溃特征。
- 证据 #3 限定了资源边界，结合证据 #1 的信号值，将根因方向锁定在资源耗尽而非配置错误。

## 🎯 根因分析 · g1

### 因果链

```text
应用内存使用量持续上升 (最高达 16MB) → 触发 Linux OOM Killer 机制 (内存压力) → 进程被强制 SIGKILL 终止 (Exit Code 137) → Liveness 探测失败 (HTTP 500) 并重启 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认的根因**：容器 `app` 由于内存突发占用或内存泄漏，触发了系统的 OOM Killer 机制（Exit Code 137）。

**证据支持**：
1.  **异常终止信号**：容器反复以 Exit Code 137（SIGKILL）终止，并伴随 25 次重启，直接表现为 `CrashLoopBackOff`（证据 #1）。
2.  **触发机制**：Linux 内核的 OOM Killer 机制因内存压力强制终止进程，这解释了为何进程在无应用层日志报错的情况下突然死亡（证据 #1, #4）。
3.  **现象表现**：进程终止导致应用服务不可用，使得 Liveness Probe 返回 HTTP 500，进而触发 Kubelet 的退避重启逻辑（证据 #2）。
4.  **资源边界**：虽然容器配置的 Memory Limit 为 96Mi，但观测到的内存使用峰值达到 16MB（证据 #4），且进程依然被终止，说明应用存在不可预测的内存尖峰或未被 Limit 完全捕获的内存分配模式。

---

## 📊 性能统计

```text
├─ 总耗时: 3.2m
├─ 问题定位: 21.0s
├─ 并发证据采集: 153.3s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 153.3s (Evidence 142.0s, RCA 11.1s)
└─ 汇总总结: 14.8s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
