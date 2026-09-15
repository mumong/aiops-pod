## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Pod aiops-case-v15/workload处于CrashLoopBackOff状态，容器反复退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Event | Reason: OOMKilled | 确认 Pod 终止的直接原因是内核 OOM Killer 介入 |
| 2 | K8s State | K8s State | container.last_terminated_reason: OOMKilled | 证实容器最后一次退出的终止信号 |
| 3 | K8s State | K8s State | container.last_exit_code: 137 | 标准 OOM Killer 退出码，与 OOMKilled 现象一致 |
| 4 | K8s State | K8s Config | container.resource_limit.memory: 64Mi | 容器被施加的硬内存限制（上限） |
| 5 | K8s State | K8s Config | container.resource_request.memory: 8Mi | 容器申请的内存保留量 |
| 6 | Logging | ES | log.message: "startup allocation 256Mi" | 证明应用进程在启动阶段试图分配 256Mi 内存，远超 64Mi 限制 |
| 7 | Metric | Prometheus | kube_pod_container_status_restarts_total: 7 | 反映容器经历了持续且频繁的崩溃重启循环 |

**证据互证说明：**
Kubernetes 的 `OOMKilled` 状态、退出码 137 与日志中应用启动时申请 256Mi 内存的事实直接矛盾于 64Mi 的容器内存硬限制（Limit）。这种资源申请超过 Cgroup 硬限制的行为直接触发了内核 OOM Killer，导致进程被强制终止，进而引发重启计数器增长和 CrashLoopBackOff 状态。

## 🎯 根因分析 · g1

### 因果链

```text
内存限制(64Mi) < 启动分配需求(256Mi) → 进程启动触发内核OOM Killer → 容器被强制终止(退出码137/OOMKilled) → Pod进入CrashLoopBackOff循环
```

### 根因结论

**已确认的根因：** 容器启动时申请的内存（256Mi）超过了 Pod 配置的 `memory limit`（64Mi）。

**分析说明：**
根因在于配置的资源硬限制（`resource_limit.memory`: 64Mi）无法容纳应用进程启动阶段的内存申请（日志事实 6 显示 `startup allocation 256Mi`）。当应用进程尝试分配超出 cgroup 允许的上限时，Linux 内核 OOM Killer 介入并发送 SIGKILL 信号终止进程（证据 1, 2, 3）。由于配置为自动重启，容器不断经历崩溃与重启，从而表现为 CrashLoopBackOff 状态（证据 7）。

---

## 📊 性能统计

```text
├─ 总耗时: 9.6m
├─ 问题定位: 18.1s
├─ 并发证据采集: 547.2s
│  └─ g1 aiops-case-v15/workload: 547.2s (Evidence 539.4s, RCA 7.7s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
