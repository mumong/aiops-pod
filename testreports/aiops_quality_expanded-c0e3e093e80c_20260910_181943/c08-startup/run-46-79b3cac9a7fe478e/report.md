## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning BackOff restarting failed container app` (x535 over 117m) | 证实异常组现象为反复崩溃 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason: OOMKilled` | 证实最近一次崩溃机制 |
| 3 | K8s State | kubernetes | `Exit Code: 137` | 配合 OOMKilled 机制，证实进程被系统强制终止 |
| 4 | K8s Config | kubernetes | `container.app.memory limit: 64Mi` | 确认该容器的硬内存限制，构成 OOM 的必要条件 |
| 5 | Logging | elasticsearch | `log.message: startup allocation 256Mi` | 证实容器在启动阶段尝试分配 256Mi 内存 |
| 6 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason=1` (reason=OOMKilled) | Metric 维度印证容器终止原因为 OOM |

**证据链说明：**
事实 #4 提供的 `64Mi` 硬限制与事实 #5 记录的 `256Mi` 启动分配量存在直接的数量级冲突。事实 #2 和 #3 表明这种资源违规触发了 Linux OOM Killer 机制。事实 #1 证实该机制导致容器进入 `CrashLoopBackOff` 循环。Metric 事实 #6 从聚合指标维度确认了终止状态。

## 🎯 根因分析 · g1

### 因果链
```text
容器启动脚本尝试分配 256Mi 内存 (Logging) → 超过 64Mi 的 memory limit 硬限制 (K8s Config) → 触发 OOMKilled (Exit Code 137) (K8s State) → CrashLoopBackOff (K8s Event)
```

### 根因结论
已确认根因为：**Pod 配置了过小的内存限制，无法容纳启动脚本的内存需求**。

具体而言，容器 `aiops-case-v15/workload` 中的 `app` 容器在启动脚本中尝试分配 `256Mi` 内存（见事实 #5），但该容器的 `memory limit` 被硬限制配置为仅 `64Mi`（见事实 #4）。这种分配量远超限制的情况导致 Linux 内核 OOM Killer 立即终止了该进程（Exit Code 137，见事实 #3 和事实 #2），进而引发 Kubernetes 不断重启容器，表现为 `CrashLoopBackOff` 状态（见事实 #1）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 14.7s
├─ 并发证据采集: 39.1s
│  └─ g1 aiops-case-v15/workload: 39.1s (Evidence 30.4s, RCA 8.4s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
