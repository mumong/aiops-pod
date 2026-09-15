## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | OOMKilled | Pod aiops-case-v15/workload 处于 CrashLoopBackOff 状态，反复被 OOMKilled |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.last_terminated_reason` | `OOMKilled` (fact-087d5062ec80) | 确认 Pod 被终止的根本原因是内存超限 |
| 2 | K8s Config | `container.resource_limit.memory` | `64Mi` (fact-2da266265e6b) | 确认容器的内存硬限制为 64Mi |
| 3 | K8s Config | `container.resource_request.memory` | `8Mi` (fact-1a1e63143f75) | 确认容器的内存请求为 8Mi，远低于 Limit |
| 4 | Logging | `log.message` | `startup allocation 256Mi` (fact-0e0f3b5f125d) | 记录应用启动时申请 256Mi 内存，直接证实资源需求超过硬限制 |
| 5 | K8s State | `container.last_exit_code` | `137` (fact-032c33c35f66) | 确认退出码 137，符合 OOM Killer 的信号特征 (128+9) |
| 6 | K8s Event | `event.message` | `Back-off restarting failed container app` (fact-4bd7601bb6ba) | 确认容器正在经历 CrashLoopBackOff 循环 |
| 7 | Metric | `container_memory_working_set_bytes` | 3334144 bytes (~3.18Mi) (fact-bc5944aecb99) | 采集时内存驻留量未触及限制，因 OOM 发生在启动瞬间且未保留持久指标 |
| 8 | Metric | `kube_pod_container_resource_limits` | 67108864 bytes (64Mi) (fact-570a0df4623e) | 从 Prometheus 确认内存限制数值与 Kubernetes 配置一致 |

**证据说明：**
1.  **内存限制与应用行为的冲突**：配置证据显示容器的内存硬限制（Limit）为 64Mi（证据 #2, #8），而日志证据记录应用启动时分配了 256Mi 内存（证据 #4）。由于 256Mi 远大于 64Mi 的限制，该行为必然触发内核 OOM Killer。
2.  **状态与日志的互相印证**：Kubernetes 状态显示 Pod 被 `OOMKilled` 且退出码为 `137`（证据 #1, #5），这与应用分配超大内存导致被杀的逻辑完全一致，同时也解释了当前的 `CrashLoopBackOff` 循环状态（证据 #6）。
3.  **指标缺失的解释**：虽然 Prometheus 采集到内存驻留量较低（约 3.18Mi，证据 #7），但由于 `sample_count=1` 无法构建趋势，且 OOM 发生在分配内存的瞬间，导致在 OOM 发生前未能捕获逼近 64Mi 的内存峰值；但这并不妨碍基于配置和日志的确定性判断。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动分配 256Mi 内存 → 突破 64Mi memory limit → 触发内核 OOM Killer (exit_code 137) → CrashLoopBackOff
```

### 根因结论

已确认根因为：**容器内存配置不足导致 OOMKilled**。

具体而言，Pod `aiops-case-v15/workload` 的应用逻辑在启动时尝试分配 **256Mi** 内存（证据 #4），而 K8s 资源配置中该容器的 `memory limit` 仅为 **64Mi**（证据 #2）。这一资源缺口触发了 Linux 内核的 OOM Killer 机制，导致容器进程被强制终止（证据 #1, #5）。随后 Kubelet 根据重启策略不断重启容器，最终表现为 `CrashLoopBackOff` 状态（证据 #6, #9）。正式 RCA 结论与收集到的真实工具事实完全一致，无需其他补充证据。

---

## 📊 性能统计

```text
├─ 总耗时: 11.9m
├─ 问题定位: 22.2s
├─ 并发证据采集: 676.2s
│  └─ g1 aiops-case-v15/workload: 676.2s (Evidence 667.3s, RCA 8.7s)
└─ 汇总总结: 14.1s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-oomkilled
