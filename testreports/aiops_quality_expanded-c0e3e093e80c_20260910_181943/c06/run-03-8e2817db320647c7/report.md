## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod workload-7679bcf76-n5vp8 处于 CrashLoopBackOff 状态，容器持续以 exitCode 2 异常退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning BackOff 36s (x22 over 5m36s) Back-off restarting failed container app` | 确认容器因反复失败而进入退避重启循环 |
| 2 | K8s State | Container | `last_terminated_reason: Error`, `last_exit_code: 2`, `restart_count: 5` | 明确容器异常终止且已退出 |
| 3 | K8s Event | K8s Condition | `ContainersNotReady: containers with unready status: [app]` | 反映容器未就绪的系统级状态 |
| 4 | Logging | Application | `[18:32:07 - 18:34:01]` 记录 `http_request` 错误：`http_status: 500`, `message: "runtime process exiting"`, `path: /work` | 记录应用代码逻辑异常引发 500 错误及进程退出机制 |
| 5 | Tracing | Tempo/Deepflow | Trace ID: `2dd9f885e1fe4020413b18846148bc2c` 对应 `GET /work` 成功 (200)，同时存在关联的 `GET /work` 失败 (500) 请求流 | 关联日志与追踪，证实 `2dd9...` 为成功请求，500 错误由同类请求引发，确认服务内部逻辑缺陷 |

**证据说明：**
- K8s 状态（#2）与日志（#4）相互印证：日志中明确记载的 `runtime process exiting` 与 `exitCode 2` 及 K8s 的 `terminated_reason: Error` 一致。
- 日志（#4）中记录的 500 错误及进程退出是触发 K8s 重启（#1）的直接原因。
- 追踪数据（#5）展示了同一服务路径 `/work` 在不同请求下出现 200 和 500 的状态，表明故障为应用内部逻辑缺陷而非网络或资源耗尽导致。

## 🎯 根因分析 · g1

### 因果链

```text
代码逻辑异常：应用处理 /work 请求时抛出 500 错误 → 机制：进程触发 runtime process exiting 退出（退出码 2） → 直接失败：kubelet 重启容器失败并进入 BackOff → 用户可见现象：Pod CrashLoopBackOff
```

### 根因结论

已确认根因：应用程序在处理 `/work` 路径的请求时存在逻辑异常。

- **原因确认**：应用日志记录了 `http_status: 500` 和 `runtime process exiting`（证据 #4），直接导致容器以 `exitCode 2` 退出（证据 #2）。
- **结果关联**：由于容器无法稳定运行，K8s 控制器触发重启策略，但因进程再次迅速失败，导致容器进入 `CrashLoopBackOff` 状态（证据 #1）。
- **结论**：集群层面的 `CrashLoopBackOff` 是应用代码内部错误（引发 500 错误并终止进程）的直接后果。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 23.4s
├─ 并发证据采集: 48.9s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 48.9s (Evidence 39.3s, RCA 9.5s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime, pod-oomkilled
