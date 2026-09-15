## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod workload-dff5cbc6b-sjvxl 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: Error | 确证应用容器非正常退出 |
| 2 | K8s State | kubernetes | `container.last_exit_code`: 78 | 标识应用进程退出时的特定错误码 |
| 3 | K8s State | kubernetes | `container.restart_count`: 6 | 量化了重启频率，证明处于 CrashLoopBackOff 状态 |
| 4 | Logging | elasticsearch | 8 条 `CONFIG_MISSING` 错误日志 | 指出导致启动/运行失败的直接错误原因 |
| 5 | Tracing | tempo | Trace ID `a358165e4c5df7b2882c057473693f30` 的 Span 显示 `http.response.status_code`: 500, `aiops.observed_mode`: config_missing_exit | 关联日志与请求，确认业务在处理请求时因配置缺失返回 500 并终止 |
| 6 | K8s Event | kubernetes | BackOff 事件：`Back-off restarting failed container app` | 提供 Kubelet 层面重启失败的时间线佐证 |

**证据印证说明**：K8s 层面记录了容器反复以错误码 78 退出和重启的事实（证据 #1-3），应用层面的日志和 Trace 提供了退出的具体机制：在处理 `/work` 请求时检测到 `CONFIG_MISSING` 并返回 500 错误退出（证据 #4-5）。两者时间范围重叠（日志 2026-09-10T20:30-20:36，事件发生 9m29s 内），共同指向配置缺失引发的启动/运行失败及随后的 CrashLoopBackOff。

## 🎯 根因分析 · g1

### 因果链

```text
Deployment 配置挂载或环境变量定义缺失 → 应用启动/运行中检测到 CONFIG_MISSING 导致返回 500 并退出 (Exit Code 78) → Kubelet 持续重启触发 CrashLoopBackOff → Pod 处于 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为**应用部署配置不完整导致 `CONFIG_MISSING` 错误**。

应用进程在启动后（或在处理首次请求时）由于缺少必要的配置项，触发了 `CONFIG_MISSING` 错误（记录于 Logging 事实 #4 和 Tracing 事实 #5）。该错误导致进程以退出码 78（事实 #2）终止。由于 Kubernetes 配置了重启策略，Kubelet 检测到容器非正常退出后多次重启，最终因重启频率过高进入 `CrashLoopBackOff` 状态（事实 #1, #3, #6）。

缺失的决定性事实为具体的配置项名称（ConfigMap 或 Secret Key），但目前已有证据充分支持“配置缺失导致应用无法正常运行并持续崩溃”这一结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 19.0s
├─ 并发证据采集: 73.4s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 73.4s (Evidence 64.4s, RCA 8.8s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
