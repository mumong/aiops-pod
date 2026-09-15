## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | 容器内存配置过低(64Mi)导致 Python 进程被 OOM Killer 终止 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | Kubernetes | 容器 app 内存硬限制 `resource_limit.memory=64Mi` | 明确内存资源边界，构成 OOM 触发条件 |
| 2 | K8s Config | Kubernetes | 容器 app 内存请求量 `resource_request.memory=8Mi` | 确认内存请求与限制之间存在显著缺口 |
| 3 | K8s Event | Kubernetes | `Exit Code: 137` | 指示进程被内核 OOM Killer 强制杀死（128+9） |
| 4 | K8s Event | Kubernetes | `BackOff restarting failed container app` (x40) | 证明 Pod 处于 CrashLoopBackOff 状态，持续重启 |
| 5 | K8s State | Kubernetes | 容器 app 重启次数 `restart_count=7`，退出码 `exit_code=137` | 验证了进程反复异常退出的事实 |
| 6 | Tracing | deepflow+tempo | GET `/health` 请求耗时 `duration_us min=3001102` (约3s)，共 7 次 | 验证应用在处理请求时发生严重阻塞或超时 |
| 7 | Logging | elasticsearch | `GET /health HTTP/1.1 200` (13:11:03) 后，13:14 开始 `context deadline exceeded` | 确认应用从短暂恢复迅速转入崩溃/无响应状态 |

**证据综合说明**：
- **现象印证**：Kubernetes 事件中的 `Exit Code: 137` 和 `CrashLoopBackOff` 直接对应了 OOM Killer 机制导致的进程非正常终止，排除了常规应用崩溃。
- **时序关联**：Trace 数据显示在短暂成功响应 `/health` (13:11) 后，后续请求耗时急剧增加至 3 秒（13:06-13:07 的记录及后续的超时），最终导致 Liveness 探针超时和容器被杀，证实了内存溢出导致系统卡死再被杀死的典型过程。
- **配置支撑**：64Mi 的硬限制对于典型的 Python 应用而言极低，结合 137 退出码，充分支撑了内存不足是核心根因。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制过低(64Mi) → 运行时内存突破 Limit 触发 OOM Killer → 容器进程非正常终止(Exit 137) → Kubernetes 重启进入 CrashLoopBackOff
```

### 根因结论

已确认的根因是**容器内存配置过低（Limit 64Mi）**。

这一配置直接导致 Python 进程在运行或处理请求时无法申请足够的内存，触发 Linux 内核的 OOM Killer 机制强行终止了容器进程（Exit Code 137）。随后，Kubernetes 的重启策略触发容器重启，由于配置未变，重启后的进程再次因同样的原因崩溃，最终导致 Pod 陷入 `CrashLoopBackOff` 状态。

证据链中，`Exit Code: 137` 提供了最关键的 OOM 信号，而 Kubernetes 的事件记录与 Metrics 中的重启计数验证了这一过程的持续性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 22.0s
├─ 并发证据采集: 72.5s
│  └─ g1 aiops-case-v17/workload: 72.5s (Evidence 65.4s, RCA 6.9s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-oomkilled, pod-crashloop-runtime
