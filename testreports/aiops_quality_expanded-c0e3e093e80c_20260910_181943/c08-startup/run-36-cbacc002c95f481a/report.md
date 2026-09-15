## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Pod workload 处于 CrashLoopBackOff 状态，Container app 反复退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning BackOff 3m7s (x418 over 93m) ... Back-off restarting failed container app` | 确认容器 `app` 在 93 分钟内已重启 418 次，呈现典型的 CrashLoopBackOff 模式 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason: "OOMKilled"` | 直接指出容器上次退出的原因是由 OOM Killer 强制终止 |
| 3 | K8s State | kubernetes | `container.last_exit_code: 137` | 退出码 137 进一步证实进程是被系统信号 (SIGKILL) 终结，符合 OOM 特征 |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory: "64Mi"` | 确认当前容器允许使用的最大硬内存限制仅为 64 MiB |
| 5 | Logging | elasticsearch | `startup allocation 256Mi` | 记录到容器启动阶段正在进行 256 MiB 的内存分配操作 |
| 6 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason(reason="OOMKilled"): 1` | 指标数据在 2026-09-14T10:59:34 确认最终终止原因为 OOMKilled |

**证据互证说明：**
日志中显示的 256 MiB 分配请求（证据 5）显著超过了 K8s 配置的 64 MiB 硬限制（证据 4）。Kubernetes 事件（证据 1）记录的频繁重启与状态（证据 2、3）显示的 `OOMKilled` 及 `137` 退出码完全吻合，且 Metric 数据（证据 6）提供了独立于 K8s API 的同一事实确认。

## 🎯 根因分析 · g1

### 因果链

```text
容器启动时尝试分配 256Mi 内存 → 超出 64Mi 的容器 Limit 配置，触发 cgroup OOM Killer → 进程被强制终止 (Exit Code 137) → Pod 频繁重启并进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为**容器内存限制配置不足**。容器 `app` 在启动时需申请 256 MiB 内存，但 Pod 规格中配置的资源上限（`resources.limits.memory`）仅为 64 MiB。由于请求量远超硬限制，Linux 内核的 OOM Killer 在内存分配时介入并杀死了该进程，导致 Pod 处于 CrashLoopBackOff 状态。

支持该结论的关键证据包括：
- **日志证据**：记录了 256 MiB 的分配行为 [5]。
- **K8s 配置证据**：64 MiB 的 Limit 配置 [4]。
- **异常状态证据**：`OOMKilled` 原因 [2]、退出码 137 [3] 以及 418 次的 BackOff 重启事件 [1]。
- **指标证据**：确认了终止原因 [6]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.6s
├─ 并发证据采集: 41.3s
│  └─ g1 aiops-case-v15/workload: 41.3s (Evidence 32.2s, RCA 9.0s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
