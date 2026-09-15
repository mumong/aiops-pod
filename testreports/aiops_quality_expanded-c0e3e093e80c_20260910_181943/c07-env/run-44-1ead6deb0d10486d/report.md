## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod aiops-case-v10/workload 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning BackOff 25s (x375 over 80m)` kubelet `Back-off restarting failed container app in pod workload_aiops-case-v10` | 确认 Pod 已进入 CrashLoopBackOff，且重启失败已持续 80 分钟 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason: Error` | 指示上一次容器实例以 Error 状态退出 |
| 3 | K8s State | kubernetes | `container.last_exit_code: 78` | 精确指出导致容器崩溃的进程退出码 |
| 4 | Logging | elasticsearch | `APP_REQUIRED_CONFIG environment variable is missing` | 提供直接根因证据，指出应用内部报错因环境变量缺失 |
| 5 | K8s Config | kubernetes | `container.resource_request.memory: 8Mi` | 排除内存资源限制导致 OOMKilled 的可能性 |

- 证据 4 (日志) 明确指出 `APP_REQUIRED_CONFIG` 缺失，结合证据 3 (Exit Code 78)，直接证实了容器因配置缺失而启动失败的因果链。
- 证据 1 (Event) 与证据 2 (Error) 共同印证了由于上述启动失败，kubelet 触发了指数退避重试机制，形成了当前的 CrashLoopBackOff 状态。

## 🎯 根因分析 · g1

### 因果链

```text
环境变量 APP_REQUIRED_CONFIG 未注入 Pod 定义 → 应用启动脚本检测到变量缺失并执行 sys.exit(78) → 容器持续以 Error 状态崩溃退出 → kubelet 触发 BackOff 机制进入 CrashLoopBackOff
```

### 根因结论

**已确认的根因**：`aiops-case-v10/workload` 容器启动失败并进入 CrashLoopBackOff，其根本原因是应用启动脚本依赖的环境变量 `APP_REQUIRED_CONFIG` 缺失，导致进程以退出码 78 退出（证据 1, 3, 4）。

- **证据 4** (`logging`) 捕获到的日志 `APP_REQUIRED_CONFIG environment variable is missing` 提供了直接的失败原因。
- **证据 3** (`K8s State`) 记录的上一次退出码 `78` 与上述日志中的退出行为一致。
- **证据 1** (`K8s Event`) 确认了这一连续失败已导致系统层面的 `BackOff` 和 `CrashLoopBackOff` 状态。

排除资源限制导致崩溃的可能性，因为容器请求的内存仅为 8Mi（证据 5），且日志错误指向明确的环境变量检查逻辑，而非 OOM 或资源竞争。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 14.9s
├─ 并发证据采集: 68.0s
│  └─ g1 aiops-case-v10/workload: 68.0s (Evidence 59.1s, RCA 8.8s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
