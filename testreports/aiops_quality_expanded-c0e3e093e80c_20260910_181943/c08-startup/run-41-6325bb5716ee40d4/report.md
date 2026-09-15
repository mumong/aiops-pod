## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | 容器内存限制(64Mi)远低于启动命令实际分配的内存量(256Mi)，导致内核 OOM Killer 强制终止进程 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason` = `OOMKilled` (`fact-0c26fb311fc2`) | 确认进程是被内核 OOM Killer 强制终止的 |
| 2 | K8s Config | kubernetes | `container.resource_limit.memory` = `64Mi` (`fact-0e22c24c794e`) | 提供内存硬限制参数 |
| 3 | Logging | elasticsearch | `log.message` = `startup allocation 256Mi` (`fact-016ce27a1965`) | 确认启动时内存申请量超过容器限制 |
| 4 | K8s Config | kubernetes | `container.resource_limit.cpu` = `100m` (`fact-748af3d6df3d`) | 确认非 CPU 资源引发的 CPU Throttling |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1, reason=`CrashLoopBackOff` (`fact-b94cf0f2a435`) | 确认当前异常状态为循环重启 |

1. 容器日志显示启动时申请内存为 `256Mi` (`#3`)，而 K8s 配置中设定的内存硬限制仅为 `64Mi` (`#2`)，申请量远超限制值。
2. 内核 OOM Killer 强制终止进程 (`#1`) 并退出，由于触发内存限制违规，容器随即进入 `CrashLoopBackOff` 循环重启状态 (`#5`)，证实内存配置是唯一的根因。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存配置限制(64Mi) < 启动实际分配量(256Mi) → 触发内核 OOM Killer 强制终止进程 → 容器以 Exit Code 137 退出 → 容器进入 CrashLoopBackOff 循环重启
```

### 根因结论

已确认根因为 **容器内存限制配置严重不足**。容器启动时申请了 `256Mi` 内存，但 K8s 配置的 `resource_limit.memory` 仅有 `64Mi`，导致内核 OOM Killer 强制终止了容器进程。该结论由 `OOMKilled` 终止原因 (`#1`) 与 `startup allocation 256Mi` 的日志记录 (`#3`) 互相印证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.0s
├─ 并发证据采集: 38.8s
│  └─ g1 aiops-case-v15/workload: 38.8s (Evidence 32.6s, RCA 6.1s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
