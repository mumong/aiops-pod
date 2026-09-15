## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod aiops-case-v10/workload 处于 CrashLoopBackOff 状态，容器 app 反复崩溃重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: Error; `container.waiting_reason`: CrashLoopBackOff | 确认为应用侧主动导致的启动崩溃 |
| 2 | K8s Event | kubernetes | `event.message`: "Back-off restarting failed container app" (x212 over 45m) | 确认持续且频率较高的故障循环模式 |
| 3 | K8s State | kubernetes | `container.last_exit_code`: 78 | 提供应用进程异常终止的精确退出码，指向应用层逻辑 |
| 4 | Logging | elasticsearch | `log.message`: "APP_REQUIRED_CONFIG environment variable is missing" | 直接记录应用启动时的缺失配置错误，解释进程退出原因 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 从 3.0 增长至 13.0 (sample_count=45, trend_evaluable=true) | 量化证实重启行为随时间持续发生，与 CrashLoopBackOff 状态一致 |

**证据印证关系**：
Logging 中的 "APP_REQUIRED_CONFIG environment variable is missing" 直接解释了 K8s 观察到的 Exit Code 78，证明这是由缺失环境变量触发的应用主动退出。Metric 的持续增长证实了该错误未被修正，导致 K8s 反复拉取并启动容器。K8s 的 CrashLoopBackOff 状态是这一机制的最终表现。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义中缺失环境变量 APP_REQUIRED_CONFIG → 应用启动脚本检测到变量为空 → 应用主动调用 sys.exit(78) 终止进程 → Pod 进入 CrashLoopBackOff 重启循环
```

### 根因结论

已确认根因为：Pod 定义中未配置必需的环境变量 `APP_REQUIRED_CONFIG`。

根据证据 [4]，应用日志直接报出缺失该变量；根据证据 [3]，该缺失导致应用以退出码 78 主动退出，而非因 OOM 或资源不足被系统杀死。这一机制解释了证据 [1] 中的 Error 终止原因以及证据 [2] 中持续的 CrashLoopBackOff 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 20.4s
├─ 并发证据采集: 49.7s
│  └─ g1 aiops-case-v10/workload: 49.7s (Evidence 39.5s, RCA 10.1s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-oomkilled, pod-crashloop-runtime
