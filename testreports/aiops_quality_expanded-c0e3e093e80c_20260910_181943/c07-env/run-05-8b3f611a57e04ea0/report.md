## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.last_terminated_reason: Error (app) | 确证应用非健康状态退出 |
| 2 | K8s State | Kubernetes | container.last_exit_code: 78 (app) | 提供具体的退出码，结合日志指向特定错误 |
| 3 | Logging | Elasticsearch | "APP_REQUIRED_CONFIG environment variable is missing" | 直接指出缺失的具体环境变量名 |
| 4 | K8s Event | Kubernetes | Warning BackOff: back-off 5m0s restarting failed container=app | 确证 CrashLoopBackOff 机制已生效 |
| 5 | Metric | Prometheus | kube_pod_container_status_restarts_total: 6 | 量化异常重启次数，印证持续故障 |
| 6 | K8s Config | Kubernetes | Resource limits: CPU 50m, Memory 32Mi; Requests: CPU 5m, Memory 8Mi | 排除资源硬性限制导致 OOM/Killed 的可能 |

证据表明应用因缺失环境变量 `APP_REQUIRED_CONFIG` 主动退出（Exit Code 78），导致 Kubernetes 控制器触发指数退避重启，当前正处于 CrashLoopBackOff 状态。

## 🎯 根因分析 · g1

```text
环境变量 APP_REQUIRED_CONFIG 未注入 → 应用启动检查失败并调用 sys.exit(78) → 容器因非零退出码被控制器标记为 Error → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论
确认的根因为**应用配置缺失**。Pod 容器 `app` 启动时检测到必需的环境变量 `APP_REQUIRED_CONFIG` 未定义（证据 #3），导致应用进程主动终止并返回退出码 78（证据 #2）。这一错误状态（证据 #1）触发了 Kubernetes 的重启策略，随着重启次数累积（证据 #5），最终进入 `CrashLoopBackOff` 阶段（证据 #4）。资源限制（证据 #6）显示 CPU 和内存配置并非导致故障的因素。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 13.2s
├─ 并发证据采集: 41.8s
│  └─ g1 aiops-case-v10/workload: 41.8s (Evidence 34.5s, RCA 7.1s)
└─ 汇总总结: 7.0s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
