## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Exit Code: 137; Reason: OOMKilled | 直接证明进程因内存超限被系统终止 |
| 2 | K8s Config | kubernetes | container.resource_limit.memory=64Mi | 确定导致终止的强制资源硬限制 |
| 3 | K8s State | kubernetes | container.waiting_reason=CrashLoopBackOff; exit_code=137; restart_count=14 | 描述应用因反复 OOM 导致的反复重启现象 |
| 4 | K8s Event | kubernetes | kubelet BackOff 5m0s restarting failed container; 87s (x235 over 51m) | 记录由于频繁崩溃，系统延长重启退避时间的行为 |
| 5 | Metric | prometheus | kube_pod_container_resource_limits(memory, byte)=67108864 | 独立监控指标再次确认 64 MiB (67108864 Bytes) 的内存限制值 |
| 6 | Metric | prometheus | kube_pod_container_status_last_terminated_reason(OOMKilled)=1 (样本数 51); kube_pod_container_status_restarts_total=14 (min 2.0, max 14.0) | 监控时序数据证实“内存耗尽”是该组异常长达 51 分钟观察窗口内的主要终止模式且重启数持续增长 |
| 7 | Logging | elasticsearch | log.message: "startup allocation 256Mi" | 日志记录显示应用启动时需要分配 256 MiB 内存，超出容器上限 |

证据分析：
1.  **K8s 状态与监控指标高度一致**：事实 1、2 明确指出因 64MiB 限制触发 OOM 终止（Exit 137），事实 5、6 从 Prometheus 层面独立确认了 64MiB 的硬性约束和持续的 OOM 终止记录。
2.  **日志揭示了内存冲突的直接原因**：事实 7 显示应用启动申请 256 MiB，而事实 2 确认容器仅配置 64 MiB 上限，这直接解释了事实 1 中 OOMKilled 的触发机制。
3.  **持续恶化趋势**：事实 3、4 和 6 表明该问题并非偶发，而是在 51 分钟内反复发生，导致系统退避机制介入。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 内存限制配置过低 (64 MiB) → 启动申请内存超出硬限制 (256 MiB) → OOM Killer 终止容器 (Exit 137) → CrashLoopBackOff (重启 14 次)
```

### 根因结论

已确认根因：应用内存需求与容器资源限制不匹配。
应用启动时需要分配 256 MiB 内存（事实 7），但 Pod 的 `resource_limit.memory` 硬限制仅为 64 MiB（事实 2、5）。超出限制的内存访问触发了内核 OOM Killer，导致容器进程以 Exit Code 137 被强制终止（事实 1）。由于资源限制未释放，每次重启均因同样原因失败，最终导致 `CrashLoopBackOff`（事实 3、4）和持续的监控警报（事实 6）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 27.3s
├─ 并发证据采集: 82.2s
│  └─ g1 aiops-case-v15/workload: 82.2s (Evidence 73.2s, RCA 8.8s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime, pod-oomkilled
