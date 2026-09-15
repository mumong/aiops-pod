## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod `workload` 的容器 `app` 启动命令依赖环境变量 `APP_REQUIRED_CONFIG`，但该变量在 Pod spec 中未定义（Environment Variables: <none>）。容器启动时检测到该变量缺失，执行 `sys.exit(78)` 主动退出，导致 kubelet 反复重启并进入 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 38s (x49 over 10m) kubelet Back-off restarting failed container app` | 确认 kubelet 正在反复尝试重启异常容器 `app` |
| 2 | K8s State | Kubernetes | `container.waiting_reason`: `CrashLoopBackOff`; `container.last_terminated_reason`: `Error`; `container.last_exit_code`: `78` | 定位到容器以退出码 78 终止并进入等待状态，符合特定错误码特征 |
| 3 | Logging | Elasticsearch | `2026-09-11T15:19:59.302Z` `APP_REQUIRED_CONFIG environment variable is missing` | 捕捉到启动失败时的明确应用日志，直接指向配置缺失 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: `6`; `kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"}`: `1` | 量化容器已重启 6 次，且当前正处于 CrashLoopBackOff 状态 |

**证据互证说明：**
- **状态与日志闭环**：K8s 状态 `CrashLoopBackOff` 和 `exit_code=78` 与日志中捕获到的明确报错信息 `APP_REQUIRED_CONFIG environment variable is missing` 相互印证，证实容器启动后立即因应用内部检查失败而退出。
- **持续重启机制**：日志记录的时间点与 Metric 显示的高重启计数（6次）、K8s 事件中的 BackOff 记录一致，证实了这是一个由环境变量缺失导致的持续启动循环。
- **缺失环节说明**：Tracing 维度显示为空（`absent`），但这不影响根因判断；因为应用日志（Logging）已经提供了决定性的直接错误原因，无需分布式追踪链路即可定位。

## 🎯 根因分析 · g1

### 因果链
```text
环境变量 APP_REQUIRED_CONFIG 缺失 → 应用启动脚本执行 sys.exit(78) → 容器非正常退出 → 导致 CrashLoopBackOff
```

### 根因结论
已确认的根因是 Pod `workload` 的容器 `app` 启动命令依赖环境变量 `APP_REQUIRED_CONFIG`，但该变量在 Pod spec 中未定义（Environment Variables: `<none>`）。

容器启动时检测到该关键变量缺失，执行了主动退出命令 `sys.exit(78)`（证据 `fact-8e1a793ece1f` 和 `fact-1aeaadf9bbec`）。由于启动失败，kubelet 触发了指数退避重试机制，导致容器状态转为 `CrashLoopBackOff` 且重启计数持续增加（证据 `fact-07a5bd71afd9` 和 `fact-c689f08afc30`）。现有证据完整支撑该结论，无需进一步调查。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 25.9s
├─ 并发证据采集: 40.7s
│  └─ g1 aiops-case-v10/workload: 40.7s (Evidence 33.5s, RCA 7.1s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
