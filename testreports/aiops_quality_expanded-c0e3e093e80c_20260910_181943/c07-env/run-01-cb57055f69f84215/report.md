## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning BackOff ... Back-off restarting failed container app ... (x7 over 84s)` | 确认容器 `app` 因反复退出触发 Kubernetes 的重启退避机制 |
| 2 | K8s State | container | `last_terminated_reason: Error`, `last_exit_code: 78` | 提供直接的应用程序退出原因与退出码 |
| 3 | Logging | elasticsearch | `APP_REQUIRED_CONFIG environment variable is missing` | 明确指出导致应用启动失败的具体缺失配置 |
| 4 | K8s Event | kubelet | `Reason: CrashLoopBackOff` | 将上述事件归类为标准的重启故障 |
| 5 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason(app, Error): 1` | 独立印证容器最后一次终止状态为 Error |
| 6 | K8s State | pod | `restart_count: 3` (aggregation, record_count: 2) | 证实故障已持续存在并经历了多次重启周期 |

上述 K8s 状态与日志提供了互相印证的因果证据：应用因缺失环境变量（日志）而主动退出（Code 78），进而触发集群的 Back-off 重启事件（K8s Event），最终导致 Pod 处于 CrashLoopBackOff 状态。

## 🎯 根因分析 · g1

### 因果链

```text
缺少环境变量 `APP_REQUIRED_CONFIG` → 应用启动读取失败 → 主动执行 sys.exit(78) → 触发 Backoff 重启
```

### 根因结论

已确认的根因是 Pod 容器 `app` 的启动配置中遗漏了必需的环境变量 `APP_REQUIRED_CONFIG`。

应用启动时因该变量缺失而执行 `sys.exit(78)`（见 Logging fact #3），导致进程以异常退出码 78 终止（见 K8s State fact #2）。Kubernetes 监控系统捕获到该终止状态（Metric fact #5），并启动了指数退避的重启策略，导致集群观察到 `CrashLoopBackOff` 症状（见 K8s Event fact #1, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 27.4s
├─ 并发证据采集: 80.2s
│  └─ g1 aiops-case-v10/workload: 80.2s (Evidence 72.2s, RCA 7.8s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime, pod-oomkilled, pod-config-error
