## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Application logic error in /work endpoint causing unhandled runtime exception |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` (fact-0ec28c3be2ce) | `Warning BackOff 4m4s (x44 over 14m) ... Back-off restarting failed container app` | 确认应用容器 `app` 处于持续崩溃重启的异常循环中 |
| 2 | K8s State | `kubernetes` (fact-3d7fca3e65d3) | `exit_code: 2` | 提供进程退出的直接信号，指示非正常终止（通常为非零退出码） |
| 3 | Logging | `elasticsearch` (fact-365030371a42等) | `{"event":"http_request", "level":"error", "message":"runtime process exiting", "path":"/work", "http_status": 500}` | 核心故障证据，明确指出在 `/work` 接口处理期间发生运行时进程退出，且伴随 HTTP 500 响应 |
| 4 | K8s State | `kubernetes` (fact-acf2d6a6601b) | `container.last_terminated_reason: Error` | 确认容器终止原因为 Error，排除因 OOM 等外部因素导致的正常重启 |
| 5 | Tracing | `deepflow` (fact-233cd6bf24fd等) | `GET /work -> 200`, duration 16863us~67813us | 作为对比基线，证明应用对 `/work` 接口的正常响应耗时范围，区分健康与异常请求 |
| 6 | Tracing | `tempo` (fact-0bb56c36f3d0) | `GET /work -> 200`, mode: `runtime_exit` | 进一步佐证应用逻辑处理过程中触发了内部退出机制，尽管响应码为200（或为异常前的日志记录），确认了应用层的行为特征 |

**证据总结：**
K8s 状态（退出码 2、BackOff）与日志（"runtime process exiting", 500错误）高度一致，共同指向 `/work` 端点的内部应用逻辑缺陷。日志中明确指出了导致容器退出的错误模式，而非资源不足或网络问题。

## 🎯 根因分析 · g1

### 因果链

```text
/app 端点 /work 处理中的未捕获运行时异常 → 进程直接退出 (exit_code 2) → K8s 重启策略触发 (CrashLoopBackOff) → 服务不可用，持续报 BackOff 警告
```

### 根因结论

**已确认的根因：**
应用代码中存在未处理的运行时逻辑错误。当处理针对 `/work` 路径的 HTTP 请求时，程序内部抛出异常导致进程直接终止（Exit Code 2）。这一行为在日志中通过 `runtime process exiting` 被明确记录（证据 #3），并由 Kubernetes 的 `CrashLoopBackOff` 状态（证据 #1, #4）和退出码（证据 #2）形成闭环验证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 17.0s
├─ 并发证据采集: 58.6s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 58.6s (Evidence 53.9s, RCA 4.7s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
