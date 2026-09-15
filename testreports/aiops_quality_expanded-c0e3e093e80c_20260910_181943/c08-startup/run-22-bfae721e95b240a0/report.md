## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Pod aiops-case-v15/workload 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason` (app): `CrashLoopBackOff`; `container.last_terminated_reason` (app): `OOMKilled`; `restart_count`: 16 | 确立 Pod 处于因 OOM 崩溃而反复重启的异常状态 |
| 2 | K8s State | kubernetes | `container.resource_limit.memory` (app): `64Mi`; `container.last_exit_code` (app): `137` | 指出容器存在硬内存限制，且进程以 SIGKILL 信号终止 |
| 3 | Logging | elasticsearch | 2026-09-14T10:18:33.608Z: `"startup allocation 256Mi"` | 揭示应用启动阶段实际需要分配的内存量（256Mi） |
| 4 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason`: `1` (OOMKilled); `kube_pod_container_status_waiting_reason`: `1` (CrashLoopBackOff) | 监控侧独立印证了容器最近一次终止原因为 OOM 且当前处于等待重启状态 |

**证据说明：**
- K8s State (#1, #2) 确认了 Pod 的异常形态（CrashLoopBackOff + Exit 137）及其根本触发机制（OOMKilled）。
- Logging (#3) 提供了应用侧的实际行为数据，证明启动阶段所需的 256Mi 内存远远超出了 State (#2) 中配置的 64Mi 限制，形成了直接的供需矛盾证据。
- Metric (#4) 与 State (#1) 的观测结果完全一致，排除了单一数据源采集错误的可能。

## 🎯 根因分析 · g1

### 因果链

```text
内存限制 (64Mi) 与启动分配 (256Mi) 严重不匹配 → 触发内核 OOM Killer 导致容器被杀 (OOMKilled) → 容器崩溃退出 (Exit Code 137) 并触发 Kubelet 重启策略 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为**容器内存配置限制过低**。

Pod `aiops-case-v15/workload` 中 `app` 容器被配置的硬内存上限为 `64Mi`（Evid 2），但应用日志明确显示其启动分配时请求了 `256Mi`（Evid 3）。该配置差异导致容器在启动初期立即超出内存配额，触发了 Linux 内核的 OOM Killer 机制，强制终止进程并返回 `Exit Code: 137`（Evid 2, Evid 1）。Kubelet 随后按照重启策略尝试重启容器，因内存配置未变，进程再次被杀，最终导致 Pod 进入 `CrashLoopBackOff` 状态（Evid 1, Evid 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.7s
├─ 并发证据采集: 47.8s
│  └─ g1 aiops-case-v15/workload: 47.8s (Evidence 38.9s, RCA 8.7s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
