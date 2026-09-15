## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod `aiops-case-v10/workload` 的容器配置中缺失环境变量 `APP_REQUIRED_CONFIG`，导致应用启动脚本检测到配置缺失后主动调用 `sys.exit(78)` 退出容器。由于 `restartPolicy` 设置为 `Always`，容器失败后 Kubernetes 不断尝试重启，从而形成 `CrashLoopBackOff` 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | Kubernetes | 容器 `app` 环境变量中缺少 `APP_REQUIRED_CONFIG` (Environment: <none>) | 指出启动所需的必要配置项缺失，是应用异常的潜在前置条件。 |
| 2 | Logging | Elasticsearch | `APP_REQUIRED_CONFIG environment variable is missing` (时间 2026-09-11T15:35:29.203Z) | 确认应用进程因环境变量缺失触发主动退出逻辑。 |
| 3 | K8s State | Kubernetes | 容器 `app` 退出码 (exit_code) 为 78；终止原因为 `Error` (fact-7da4fbd973d8) | 验证退出行为与日志描述一致，且非由 OOM 等系统原因导致。 |
| 4 | K8s Event | Kubernetes | `BackOff restarting failed container app in pod workload_aiops-case-v10` (事实 6 次聚合) | 确认 K8s 控制面已捕获失败并重试机制启动。 |
| 5 | K8s State | Kubernetes | 容器 `app` 状态为 `CrashLoopBackOff`，已重启 9 次 (fact-23b4780f1c40) | 确认当前故障处于持续循环状态。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 值为 9，状态 `CrashLoopBackOff` (fact-ce6b0482dd54, fact-aa40572683a2) | 从监控层面独立印证了容器的重启频次与当前状态，与 K8s 状态一致。 |

**证据关联与印证：**
K8s 事件与状态直接反映了 `CrashLoopBackOff` 的现象，Metric 数据在数值上完全一致。关键的根因链条由 Logging 中的明确错误信息（缺失变量）与 K8s 记录的特定退出码（78）互相支撑，共同指向应用层配置缺失而非底层资源或调度问题。

## 🎯 根因分析 · g1

### 因果链

```text
环境变量配置缺失 (APP_REQUIRED_CONFIG) → 应用启动检查失败触发主动退出 (sys.exit(78)) → 容器异常终止 (Exit Code 78) → 重启策略驱动持续重试形成 CrashLoopBackOff
```

### 根因结论

已确认的根因为：Pod `aiops-case-v10/workload` 的容器配置中缺失了环境变量 `APP_REQUIRED_CONFIG`。

这一配置缺陷导致应用启动脚本检测不到必需的环境变量，从而执行主动退出逻辑（`sys.exit(78)`）。Kubernetes 记录该次终止为 Error（证据 #3），随后因默认重启策略再次拉起容器。新容器启动后遇到同样的配置缺失问题，导致不断重启。这一过程被 Kubernetes 事件（证据 #4）标记为 BackOff，并持续处于 `CrashLoopBackOff` 状态（证据 #5, #6）。

---

## 📊 性能统计

```text
├─ 总耗时: 9.5m
├─ 问题定位: 16.1s
├─ 并发证据采集: 545.7s
│  └─ g1 aiops-case-v10/workload: 545.7s (Evidence 537.4s, RCA 8.2s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
