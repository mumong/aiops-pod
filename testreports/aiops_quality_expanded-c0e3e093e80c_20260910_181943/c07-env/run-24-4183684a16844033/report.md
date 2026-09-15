## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod workload in aiops-case-v10 is in CrashLoopBackOff state with exit code 78 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Back-off restarting failed container app in pod workload_aiops-case-v10(d3e0dc86-6f8b-4f29-a50c-826bf2a1f1e6) (over 47m) | 确认 Pod 进入指数退避重启循环 |
| 2 | K8s State | kubernetes | Last terminated reason: Error; Current waiting reason: CrashLoopBackOff | 确认容器异常终止且当前处于不可用状态 |
| 3 | K8s State | kubernetes | Container app last exit code: 78; Restart count: 14 | 提供具体的异常退出码与重启频次证据 |
| 4 | Logging | elasticsearch | "APP_REQUIRED_CONFIG environment variable is missing" | 直接指出容器启动失败的根本原因 |
| 5 | Metric | prometheus | kube_pod_container_status_restarts_total: 3.0 → 13.0 (47 samples) | 验证重启行为在观察窗口内持续发生 |
| 6 | Metric | prometheus | kube_pod_container_status_waiting_reason (CrashLoopBackOff) & last_terminated_reason (Error) 持续为 1 | 从监控视角确认了持续的异常终止等待状态 |

**证据说明：**
Kubernetes 状态与事件确认了 Pod 处于 CrashLoopBackOff 状态且容器以 Exit Code 78 异常退出。日志事实直接定位到缺失环境变量 `APP_REQUIRED_CONFIG` 这一启动失败原因。Metric 数据中的重启总数上升趋势与 Kubernetes 的 14 次重启计数及持续报错状态高度一致，佐证了故障的持续性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 中缺失环境变量 APP_REQUIRED_CONFIG → 应用启动脚本检测到配置缺失并报错 → 调用 sys.exit(78) 终止进程 → Kubelet 发现容器退出并触发 CrashLoopBackOff 退避重启循环
```

### 根因结论

**已确认根因：** 容器应用因启动脚本依赖的环境变量 `APP_REQUIRED_CONFIG` 缺失而显式调用退出（Exit Code 78）。

该配置缺失导致应用启动即终止，Kubernetes 检测到 Exit Code 78 的异常退出后，按照 BackOff 策略反复重启容器，最终导致 Pod 进入 `CrashLoopBackOff` 状态且状态持续 `ContainersNotReady`。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 22.0s
├─ 并发证据采集: 36.1s
│  └─ g1 aiops-case-v10/workload: 36.1s (Evidence 28.7s, RCA 7.3s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime, pod-oomkilled
