## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Pod `workload-7679bcf76-jwr8b` 处于 CrashLoopBackOff 状态，持续重启失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff; `container.restart_count`: 11 | 确认 Pod 处于持续重启且不可用的状态 |
| 2 | K8s Event | kubernetes | `BackOff` 事件：157次（持续36m），消息 `back-off 5m0s restarting failed container=app` | 确认 Kubelet 正在按指数退避策略重启失败容器 |
| 3 | K8s State | kubernetes | `container.last_terminated_reason`: Error; `container.last_exit_code`: 2 | 确定上一次容器退出的根本原因是进程异常终止（非 OOMKilled） |
| 4 | Logging | elasticsearch | Pattern `runtime process exiting` (4次, trace_ids: ff8dadf1.../aa8198c7...) | 直接观察到应用进程主动触发退出逻辑，且退出前内存分配为 0MiB |
| 5 | Tracing | tempo | Trace `658aa1692c4efa6e14572426a6c4198e`, 属性 `aiops.observed_mode: runtime_exit`, HTTP 状态 500 | 确认最后一次故障请求被标记为“运行时退出”模式，与日志证据完全对应 |

**证据关联说明：**
Kubernetes 的 Exit Code 2 与 Tracing 中的 `runtime_exit` 模式直接印证了应用进程是主动退出而非被动杀死；日志中 `allocated_mib` 为 0 排除了内存硬限制导致的 OOMKilled 嫌疑，指向应用内部逻辑。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置 FAILURE_MODE=runtime_exit → 请求 /work 时主动调用退出逻辑 (Exit Code 2) → Kubelet 捕获容器异常终止并触发重启 → Pod 进入 CrashLoopBackOff
```

### 根因结论

已确认根因：**应用被显式配置为 `FAILURE_MODE=runtime_exit`**。

该配置导致应用在处理 `/work` 请求时主动终止自身进程（Exit Code 2），Kubelet 随后将其判定为错误并触发重启，进而导致 Pod 陷入 `CrashLoopBackOff` 状态。

**关键证据支撑：**
- **Tracing** 明确标记了 `aiops.observed_mode: runtime_exit`，证实退出行为是应用逻辑的一部分，而非外部强制操作或系统资源耗尽（如 OOM）。
- **Logging** 中的 `runtime process exiting` 模式进一步确认了这一点。

---

## 📊 性能统计

```text
├─ 总耗时: 9.2m
├─ 问题定位: 17.0s
├─ 并发证据采集: 525.5s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 525.5s (Evidence 517.6s, RCA 7.7s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime, pod-oomkilled, pod-config-error, pod-notready-probe-failed
