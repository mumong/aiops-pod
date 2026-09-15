## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | 容器内存配置错误：资源限制（limit 64Mi）远低于应用启动时申请的内存（256Mi），导致 Linux OOM Killer 反复终止容器，引发 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | kubernetes | container `app` resource_limit.memory: `64Mi` (fact-d110455f63f2) | 确认资源硬限制极低 |
| 2 | Logging | elasticsearch | startup allocation `256Mi` (fact-016ce27a1965) | 确认应用启动内存需求远超容器限制 |
| 3 | K8s Event | kubernetes | Last terminated reason: `OOMKilled`, Exit Code: `137` (fact-5c57f179be4a, fact-140fef9d763c) | 确认进程被操作系统强制终止且原因确切 |
| 4 | K8s State | kubernetes | Container waiting reason: `CrashLoopBackOff`, restart_count: `21` (fact-1bed0d398156, fact-37ab4e25d46d) | 确认异常现象及高频重启 |
| 5 | Metric | prometheus | kube_pod_container_status_last_terminated_reason (OOMKilled) 和 kube_pod_container_status_waiting_reason (CrashLoopBackOff) 均为 1 (fact-1c18d84fc07f, fact-a68fac585f5f) | 验证容器处于 OOM 导致崩溃循环的当前状态 |

**证据分析：**
Kubernetes 配置（证据 1）显示内存限制为 64Mi，而日志（证据 2）表明应用启动需要分配 256Mi。这种“申请 > 限制”的严重不匹配直接触发了 Linux OOM Killer，导致容器以 137 号错误退出（证据 3）。这种反复被杀导致的状态（证据 4）已被 Prometheus 指标（证据 5）独立确认，形成了完整的故障闭环。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存配置错误 (limit 64Mi < 申请 256Mi) → Linux OOM Killer 终止应用进程 (Exit Code 137) → 容器频繁重启 (21次) → 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为**容器内存资源限制配置过低**。
具体而言，Pod `aiops-case-v15/workload` 中容器 `app` 的 `resource_limit.memory` 被硬限制为 `64Mi`（证据 1），但该应用在启动时即尝试分配 `256Mi` 内存（证据 2）。由于硬性限制（Hard Limit）低于启动申请值，Linux OOM Killer 介入并强制终止了该进程（证据 3）。kubelet 检测到容器退出后反复重启，最终判定其不可用，导致 Pod 进入 `CrashLoopBackOff` 状态（证据 4），该状态由 Prometheus 监控指标（证据 5）实时确认。现有证据（K8s 配置、日志、指标）互相印证，结论成立。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 12.7s
├─ 并发证据采集: 47.9s
│  └─ g1 aiops-case-v15/workload: 47.9s (Evidence 38.8s, RCA 8.9s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
