## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Pod aiops-case-v15/workload 处于 CrashLoopBackOff 状态，容器 app 频繁重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | 容器 `app` 最后终止原因为 `OOMKilled` (fact-22c51c730d6e) | 直接指出进程被内核 OOM Killer 终止 |
| 2 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason` 标记为 `OOMKilled` (fact-839e85ae8237) | 从监控侧独立验证了终止原因 |
| 3 | K8s State | kubernetes | 容器 `app` 退出码为 `137` (fact-8846f5fa2aee) | 确认进程被强杀（SIGKILL）的状态码 |
| 4 | K8s State | kubernetes | 容器 `app` 当前处于 `CrashLoopBackOff` (fact-cf730630755a) | 确认当前持续的故障状态 |
| 5 | K8s Event | kubernetes | kubelet 记录 `Back-off restarting failed container` (fact-a67c001ea9e3) | 记录重启频率与持续时间 |
| 6 | K8s Config | kubernetes | 容器 `app` 内存限制 (limit) 为 `64Mi` (fact-66fe89bd67b6) | 提供资源配额边界，是 OOM 的直接诱因 |
| 7 | Logging | elasticsearch | 应用日志 `startup allocation 256Mi` (fact-016ce27a1965) | 证明应用启动时需求远超 64Mi 限制 |

**证据关联说明：**
K8s 状态与监控指标一致确认了 `OOMKilled` 和 `Exit Code: 137`（证据 #1, #2, #3）。K8s 配置（证据 #6）与日志（证据 #7）直接构成冲突：容器被限制在 64Mi，但应用启动即尝试分配 256Mi，这种资源瓶颈必然触发 Linux 的 OOM 机制，进而导致证据 #4 和 #5 中的反复重启。

## 🎯 根因分析 · g1

### 因果链

```text
内存限制(64Mi)与应用需求(256Mi)不匹配 → 触发 Linux OOM Killer → 进程被 SIGKILL (Exit Code 137) → 进入 CrashLoopBackOff
```

### 根因结论

已确认根因为**容器资源限制配置过低**。

应用 `aiops-case-v15/workload` 的容器 `app` 被硬限制为 `64Mi` 内存，但其启动日志显示需要分配 `256Mi`。这种不匹配导致进程在执行内存分配时触发 Linux OOM Killer 机制（事实支持：证据 #1, #2, #6, #7）。操作系统强制终止进程（Exit Code 137）导致 K8s 重启失败并进入 CrashLoopBackOff（事实支持：证据 #4, #5）。现有证据链完整，无需更多事实即可定性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 13.7s
├─ 并发证据采集: 43.1s
│  └─ g1 aiops-case-v15/workload: 43.1s (Evidence 34.5s, RCA 8.5s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
