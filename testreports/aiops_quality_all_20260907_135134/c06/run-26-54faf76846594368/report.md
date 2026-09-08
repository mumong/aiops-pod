## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | 应用代码在处理 HTTP 请求 `/work` 时触发未捕获的致命错误，导致 Python 进程主动终止（exitCode=2），进而引发 Pod CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: `CrashLoopBackOff`, `exit_code`: 2 | 确认容器因代码逻辑终止（exitCode=2）陷入重启循环，直接锁定故障机制 |
| 2 | Logging | elasticsearch | `http_request` 模式：路径 `/work`，`runtime process exiting`，`http_status: 500`，`occurrence_count: 4` | 记录到应用层致命错误日志，确认终止源于 `/work` 业务逻辑处理失败 |
| 3 | K8s Event | kubernetes | `BackOff`: `Back-off restarting failed container app in pod workload-7679bcf76-jwr8b` (x316 over 72m) | 展现长期的重启震荡现象，佐证代码错误持续触发且未被自愈 |
| 4 | Tracing | tempo/deepflow | `GET /work` 的 500 Span (`trace_id: cbadac50855f5a9fdc68ea695812457d`) 且 `aiops.observed_mode: runtime_exit`；伴随成功 200 请求 | 区分了代码崩溃与正常运行：崩溃请求表现为进程退出，而 `/work` 路径本身可成功（200），排除全量业务不可用 |

证据表明 `workload-7679bcf76-jwr8b` 的 Pod 持续重启。Tracing 中的 500 请求与日志中的 `runtime process exiting` 直接对应（同属 `/work` 路径），而 K8s 的 `exitCode=2` 证实了代码层面的未捕获异常。K8s 事件证实了这种崩溃导致的 BackOff 状态已持续数十分钟。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码在处理 HTTP 请求 `/work` 时触发未捕获的致命错误 → Python 进程主动终止（exitCode=2） → Kubernetes 容器因 exitCode=2 终止进入 CrashLoopBackOff → 用户发起 `/work` 请求时间歇性返回 500 且 Pod 持续重启
```

### 根因结论

已确认根因是 **应用代码在处理 `/work` 请求时触发未捕获的致命错误**（如 Python 异常或断言失败）。
- 代码层面的未捕获异常导致 Python 进程以 `exitCode=2` 主动终止（证据 #1, #2）；
- 终止事件被 K8s 容器运行时检测到，触发 Pod 自动重启，并因连续失败进入 `CrashLoopBackOff` 状态（证据 #1, #3）；
- 用户可见现象为在 Pod 启动及重启间隙，访问 `/work` 路径时接收 HTTP 500 响应，并伴随频繁的 Pod 重启事件（证据 #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 20.5s
├─ 并发证据采集: 93.7s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 93.7s (Evidence 87.7s, RCA 5.9s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
