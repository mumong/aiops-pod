## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod `workload` 的启动命令硬编码依赖环境变量 `APP_REQUIRED_CONFIG`，但该变量在容器配置中未声明（`environment: <none>`），导致进程启动时检测缺失并主动调用 `sys.exit(78)` 终止，引发 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason=CrashLoopBackOff`, `container.last_terminated_reason=Error` (fact-2caa96e63aa9, fact-71490cf019ce) | 确认 `app` 容器处于重启循环状态 |
| 2 | K8s State | Kubernetes | `container.last_exit_code=78` (fact-3142d8f9b7c3) | 定位进程异常退出的具体错误码 |
| 3 | Logging | Elasticsearch | 日志信息: "APP_REQUIRED_CONFIG environment variable is missing" (fact-1aeaadf9bbec) | 解释退出码 `78` 的来源，直接指出缺失的环境变量 |
| 4 | K8s Event | Kubernetes | `Warning BackOff ... Back-off restarting failed container app` (fact-a6b97eaeab8b) | 记录 Pod 反复重启的系统事件行为 |

证据 2（退出码 78）与证据 3（日志记录变量缺失）在时间序列和因果关系上相互印证，解释了 Pod 处于 `CrashLoopBackOff` 的根本机制。

## 🎯 根因分析 · g1

### 因果链

```text
缺少环境变量配置 → 启动命令检测缺失 → 进程主动退出 (exit 78) → CrashLoopBackOff
```

### 根因结论

已确认的根因是 Pod `aiops-case-v10/workload` 的 `app` 容器启动命令硬编码依赖 `APP_REQUIRED_CONFIG` 环境变量，但该变量在容器配置中未声明。当容器启动时，应用检测到该环境变量缺失并主动调用 `sys.exit(78)` 终止，从而触发了 K8s 的 `CrashLoopBackOff` 机制（见证据 1, 2, 3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 13.9s
├─ 并发证据采集: 46.8s
│  └─ g1 aiops-case-v10/workload: 46.7s (Evidence 40.1s, RCA 6.5s)
└─ 汇总总结: 6.8s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
