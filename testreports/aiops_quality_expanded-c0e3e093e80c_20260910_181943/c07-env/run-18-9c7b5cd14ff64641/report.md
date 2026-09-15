## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod aiops-case-v10/workload 持续 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | Kubernetes | container.resource_limit.memory: 32Mi; container.resource_request.memory: 8Mi | 排除资源溢出，内存限制充足 |
| 2 | Logging | Elasticsearch | APP_REQUIRED_CONFIG environment variable is missing | 确认导致应用崩溃的直接触发机制 |
| 3 | K8s State | Kubernetes | container.last_exit_code: 78 | 确认应用主动以特定退出码终止 |
| 4 | K8s State | Kubernetes | container.last_terminated_reason: Error | 确认容器异常终止状态 |

K8s 状态（证据 3、4）与日志（证据 2）共同指向同一个终止原因：由于缺失核心配置变量，应用代码触发退出并导致 CrashLoopBackOff。

## 🎯 根因分析 · g1

```text
Pod 容器定义缺失环境变量 APP_REQUIRED_CONFIG → 容器启动执行代码检测到 env 为空 → 进程执行 sys.exit(78) 主动终止 → Kubernetes 重启策略触发 CrashLoopBackOff
```

**根因结论**
已确认根因为“容器应用代码强制依赖环境变量 `APP_REQUIRED_CONFIG`，但 Pod 规范中未定义该变量”（参考证据 2）。这直接导致启动时获取为空，进而主动退出（参考证据 3、4），最终表现为持续 CrashLoopBackOff。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 51.5s
├─ 并发证据采集: 46.0s
│  └─ g1 aiops-case-v10/workload: 46.0s (Evidence 38.0s, RCA 7.6s)
└─ 汇总总结: 5.1s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
