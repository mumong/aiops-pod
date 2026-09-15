## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod aiops-case-v10/workload 中的 app 容器未配置必需的 APP_REQUIRED_CONFIG 环境变量，导致应用启动时主动调用 sys.exit(78) 退出，进而触发 Kubernetes 的重启机制和 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning BackOff 4m19s (x95 over 24m) kubelet Back-off restarting failed container app` | 确认容器重启行为触发了指数退避策略 |
| 2 | K8s State | kubernetes | `container.waiting_reason: CrashLoopBackOff`, `container.last_terminated_reason: Error` | 定义当前容器处于失败循环中的状态 |
| 3 | K8s State | kubernetes | `container.last_exit_code: 78` | 提供应用退出的具体代码，指向应用层主动终止 |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory: 32Mi` | 排除 OOMKilled 可能性（内存限制远小于典型 OOM 触发值） |
| 5 | Logging | elasticsearch | `APP_REQUIRED_CONFIG environment variable is missing` | 揭示导致应用退出的直接原因（环境变量缺失） |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total: first=3 -> last=9` (24 samples) | 提供重启频率指标，验证重启行为是持续的 |

**证据互证说明：**
- K8s 状态的 `CrashLoopBackOff` 结合 `exit_code=78` 表明容器并非崩溃，而是有序退出 [2][3]；Logging 记录缺失 `APP_REQUIRED_CONFIG` 解释了退出原因 [5]；Metric 显示的 `restarts_total` 增长证实了该循环在监控窗口内的持续性 [6]。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 缺少 APP_REQUIRED_CONFIG 环境变量 → 应用检测到配置缺失并调用 sys.exit(78) 主动退出 → Kubelet 持续重启容器并应用指数退避策略 → Pod 状态进入 CrashLoopBackOff 且 Ready=False
```

### 根因结论

已确认根因为 Pod `aiops-case-v10/workload` 的 `app` 容器未配置必需的 `APP_REQUIRED_CONFIG` 环境变量。

该配置缺失导致应用启动时主动检测失败并退出（Exit Code 78），这一行为持续触发 Kubernetes 的重启机制，最终表现为 `CrashLoopBackOff` 状态。这一结论由 Logging 记录的缺失提示 [5]、K8s 记录的非零退出码 [3] 以及持续的重启状态 [2][6] 共同验证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 26.0s
├─ 并发证据采集: 41.7s
│  └─ g1 aiops-case-v10/workload: 41.7s (Evidence 33.0s, RCA 8.5s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-oomkilled, pod-crashloop-runtime
