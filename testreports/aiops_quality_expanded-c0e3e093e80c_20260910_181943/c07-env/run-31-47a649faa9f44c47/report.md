## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod aiops-case-v10/workload 的容器 `app` 启动脚本依赖环境变量 `APP_REQUIRED_CONFIG`，但该环境变量未在 Pod 定义中配置（environment: <none>），导致脚本检测到变量缺失后主动调用 sys.exit(78) 终止进程，引发 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `BackOff restarting failed container app in pod workload_aiops-case-v10` (x259 over 55m) | 确认应用进入循环重启状态 |
| 2 | K8s State | Kubernetes | `exit_code: 78` | 验证容器以非零退出码主动终止 |
| 3 | K8s State | Kubernetes | `phase: Running`, `restart_count: 15` | 证实 Pod 处于运行中但容器不断重启的循环中 |
| 4 | Logging | Elasticsearch | `APP_REQUIRED_CONFIG environment variable is missing` | 提供容器因关键变量缺失直接退出的原始日志 |
| 5 | Metric | Prometheus | `last_terminated_reason: Error`, `waiting_reason: CrashLoopBackOff`, `restarts_total: 15` | 从指标视角交叉印证日志记录的 CrashLoopBackOff 状态与重启次数 |

**证据说明**：
Kubernetes 事件与指标明确记录了 `CrashLoopBackOff` 状态及 15 次重启。日志 `fact-10c09513c777` 揭示了终止原因：启动脚本检测到 `APP_REQUIRED_CONFIG` 缺失并执行 `sys.exit(78)`。该退出码 78 与 K8s 事实 `fact-864918ee82c3` 完全一致，直接证明了异常根因在于环境变量缺失导致的进程主动退出。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义缺失 `APP_REQUIRED_CONFIG` 环境变量配置 → 容器启动脚本检测到环境变量为空，执行 sys.exit(78) → 容器以非零退出码终止，Kubernetes 触发重启策略 → 容器反复退出与重启，状态进入 CrashLoopBackOff
```

### 根因结论

已确认的根因是 `aiops-case-v10/workload` Pod 的容器 `app` 在启动脚本中硬依赖环境变量 `APP_REQUIRED_CONFIG`，但该环境变量未在 Pod 定义中配置（`environment: <none>`）。
这一缺失导致容器启动时直接报错并主动以退出码 78 终止（证据编号：4, 2），进而触发 Kubernetes 的重启机制（证据编号：1, 3, 5），表现为持续的 CrashLoopBackOff 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 19.7s
├─ 并发证据采集: 45.3s
│  └─ g1 aiops-case-v10/workload: 45.3s (Evidence 35.6s, RCA 9.6s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
