## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod workload in namespace aiops-case-v10 is in CrashLoopBackOff state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning BackOff ... Back-off restarting failed container app ... x212 over 48m` | 确认容器长期循环重启，处于 CrashLoopBackOff 状态 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason: Error` | 标识容器最近一次终止原因为非零退出异常 |
| 3 | K8s State | kubernetes | `container.last_exit_code: 78` | 明确容器终止的具体错误码，指向应用程序内部逻辑终止 |
| 4 | Logging | elasticsearch | `APP_REQUIRED_CONFIG environment variable is missing` | 定位具体异常原因：应用启动脚本检查缺失关键环境变量 |
| 5 | K8s Config | kubernetes | `container.resource_limit.cpu: 50m`, `container.resource_limit.memory: 32Mi` | 资源限制已配置但非本轮异常主因（排除 OOMKill/Throttling） |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total: 14` | 确认重启计数与 K8s 侧观察一致，排除单点偶发错误 |

**证据关联说明**：
Kubernetes 事件的 `BackOff` 警告（证据 1）与 `last_terminated_reason: Error`（证据 2）共同描述了容器的宏观重启行为。日志中的具体报错信息（证据 4）解释了导致 Error 的直接原因，即应用因缺失环境变量 `APP_REQUIRED_CONFIG` 主动退出了进程，这与容器返回的 `exit_code: 78`（证据 3）完全吻合，形成完整的因果闭环。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 未定义环境变量 APP_REQUIRED_CONFIG → 容器启动脚本校验失败 → 进程主动执行 exit(78) → K8s 判定容器异常并触发 CrashLoopBackOff
```

### 根因结论

**已确认的根因**：
异常组 `g1` 的核心问题在于 `aiops-case-v10/workload` 的 Pod 配置缺失必需的环境变量。容器内的启动脚本要求存在 `APP_REQUIRED_CONFIG` 变量，由于该变量在 Pod Spec 中未定义，导致应用进程无法启动并立即以退出码 `78` 终止。Kubernetes 检测到非零退出码后，按照重试策略进行反复重启，最终进入 `CrashLoopBackOff` 状态。该结论由 `elasticsearch` 日志（证据 4）提供的具体错误信息和 `kubernetes` 侧的 `exit_code: 78`（证据 3）相互印证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 28.8s
├─ 并发证据采集: 40.1s
│  └─ g1 aiops-case-v10/workload: 40.1s (Evidence 32.7s, RCA 7.3s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
