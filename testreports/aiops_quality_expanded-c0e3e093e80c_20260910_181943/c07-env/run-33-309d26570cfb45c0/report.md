## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod aiops-case-v10/workload 处于 CrashLoopBackOff 状态，容器反复重启退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Warning BackOff 3m47s (x259 over 58m) kubelet: Back-off restarting failed container app | 确认容器进入反复重启循环 |
| 2 | K8s State | kubernetes | container.last_terminated_reason: Error, container.last_exit_code: 78 | 确认容器异常退出且退出码为 78 |
| 3 | K8s State | kubernetes | container.waiting_reason: CrashLoopBackOff | 确认 Pod 处于等待重启的阻塞状态 |
| 4 | K8s Config | kubernetes | container.resource_limit.memory: 32Mi, container.resource_limit.cpu: 50m | 确认资源限制值较低，排除显式 OOM/Kill 配置因素 |
| 5 | Logging | elasticsearch | log.message: "APP_REQUIRED_CONFIG environment variable is missing" | 直接定位容器启动失败的原因为关键环境变量缺失 |

**证据分析**：
日志事实 (第 5 条) 提供了确切的启动失败原因（缺少环境变量 `APP_REQUIRED_CONFIG`），这与容器以非零退出码 78 异常终止（第 2 条）完全吻合。该退出行为触发了 Kubernetes 的标准重启逻辑，进而演变为长周期的 BackOff 状态（第 1 条）和 CrashLoopBackOff（第 3 条）。资源配置（第 4 条）作为辅助上下文，显示资源配额并非导致当前故障的直接原因。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 未定义 'APP_REQUIRED_CONFIG' 环境变量 → 容器启动脚本校验失败并执行 sys.exit(78) → Kubernetes 检测到容器非正常退出 (Error/Exit Code 78) → kubelet 触发指数退避重启，进入 CrashLoopBackOff
```

### 根因结论

已确认根因为：**应用启动依赖关键环境变量 `APP_REQUIRED_CONFIG`，但 Pod 定义中未配置该变量**。

日志记录显示应用启动脚本检测到该环境变量缺失并主动终止（exit code 78，见证据 #2, #5）。这一启动阶段的配置缺失导致容器反复重启失败，最终被 Kubernetes 标记为 CrashLoopBackOff（见证据 #1, #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 14.4s
├─ 并发证据采集: 47.7s
│  └─ g1 aiops-case-v10/workload: 47.7s (Evidence 36.0s, RCA 11.6s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
