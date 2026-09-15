## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod aiops-case-v10/workload 处于 CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 4m5s (x375 over 84m)` | 确认容器重启进入 BackOff 阶段 |
| 2 | K8s State | Kubernetes | `last_terminated_reason: Error`, `waiting_reason: CrashLoopBackOff` | 标识主进程异常退出，等待重启 |
| 3 | K8s State | Kubernetes | `exit_code: 78` | 提供主进程退出的具体代码 |
| 4 | Logging | Elasticsearch | `APP_REQUIRED_CONFIG environment variable is missing` (2026-09-11T16:42:16Z) | 直接定位缺失环境变量及错误日志 |
| 5 | Metric | Prometheus | `waiting_reason: 1` (reason: CrashLoopBackOff), `restart_count: 21` | 从集群监控层印证容器重启与等待状态 |

**证据分析：**
日志 (第4项) 明确指出了主进程启动时因缺少 `APP_REQUIRED_CONFIG` 变量而报错，直接导致进程以 `exit_code 78` (第3项) 终止。这一异常退出被 K8s (第2项) 捕获并标记为 `Error`，进而引发 Kubelet 触发 `BackOff` 逻辑 (第1项)。Metric (第5项) 独立记录了当前的重启计数和 CrashLoopBackOff 状态，与 K8s 状态一致。

## 🎯 根因分析 · g1

### 因果链

```text
缺少 APP_REQUIRED_CONFIG 环境变量注入 (事实 #4) → Python 主进程检测缺失并打印错误日志 → 主进程调用 sys.exit(78) 异常终止 (事实 #3) → Kubelet 触发重启并进入 BackOff 导致 CrashLoopBackOff (事实 #1)
```

### 根因结论

已确认根因为 **容器配置缺失**：Pod 缺少必要的 `APP_REQUIRED_CONFIG` 环境变量，导致主进程启动失败。

- **确认依据**：日志 (证据 #4) 明确显示缺失该变量，且容器以退出码 78 终止 (证据 #3)，该退出码与代码中的 `sys.exit(78)` 直接对应。K8s 状态 (证据 #1, #2) 和 Metric (证据 #5) 均一致反映了由此引发的 `CrashLoopBackOff` 现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 14.2s
├─ 并发证据采集: 41.6s
│  └─ g1 aiops-case-v10/workload: 41.5s (Evidence 32.0s, RCA 9.4s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
