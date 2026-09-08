## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-jwr8b 持续处于 CrashLoopBackOff 状态（重启17次），无法就绪。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: CrashLoopBackOff | 确认容器因持续异常退出触发了 K8s 重启保护机制。 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason`: Error | 确认容器进程已终止，且非正常退出。 |
| 3 | K8s State | Kubernetes | `container.last_exit_code`: 2 | 提供进程退出的具体代码，表明是应用层主动退出而非被系统 OOMKill。 |
| 4 | Logging | Elasticsearch | `runtime process exiting` (5次) | 应用层核心日志，指出进程在收到请求后主动退出，缺失堆栈详情。 |
| 5 | Logging | Elasticsearch | `http_status: 500` (对应 runtime process exiting) | 证实进程退出时 HTTP 请求未成功完成，且无成功响应。 |
| 6 | Tracing | Deepflow/Tempo | `GET /work` -> `500` (1次) | 网络层捕获到一次失败请求，印证了服务处理异常。 |
| 7 | Tracing | Deepflow/Tempo | `GET /work` -> `200` + `aiops.observed_mode: "runtime_exit"` (多次) | 即使返回 HTTP 200，底层观测模式为运行时退出，说明应用可能在响应后或异步逻辑中崩溃。 |

上述证据形成了“请求处理 -> 进程异常退出 -> K8s 重启”的闭环。Log 显示的 `runtime process exiting` 结合 Trace 中的 `runtime_exit` 模式，证实了异常源于应用内部逻辑崩溃，而非 K8s 环境（如资源限制导致的 OOM）或网络层故障。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理 `/work` 请求时触发未捕获异常 → 进程记录 'runtime process exiting' 并设置退出码 2 终止 → Kubelet 捕获容器异常退出并触发重启 → CrashLoopBackOff (重启17次)
```

### 根因结论

**已确认的根因**：应用 `aiops-case-06/workload-7679bcf76-jwr8b` 在业务代码执行期间发生内部崩溃（如 Bug 或逻辑异常）。

*   **证据支撑**：
    *   Kubernetes 事实 `fact-5d158a51948c` 显示容器退出码为 `2`（通常为用户定义的错误或应用层异常）。
    *   日志事实 `fact-3f0a7c0fbefb` 等明确记录 `runtime process exiting`，直接指向应用进程自身的终止行为。
    *   Tracing 事实 `fact-49798e4ec67a` 和 `fact-496d3eb49121` 带有 `aiops.observed_mode: "runtime_exit"` 标签，与日志结论一致。

**未确认原因（证据不足）**：导致“runtime process exiting”的具体业务异常原因（例如具体的异常类型、空指针、依赖超时等）。
*   虽然日志聚合显示了该模式，但缺失具体的 Error Stack Trace（如 Java 的 `NullPointerException` 或 Python 的 `KeyError` 详情）。
*   日志事实 `fact-26904e7564c4` 显示 `allocated_mib` 始终为 0，且资源 Request/Limit 设定相对宽松（24Mi/96Mi），目前无法直接判定为 OOM。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 19.8s
├─ 并发证据采集: 89.0s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 89.0s (Evidence 77.8s, RCA 11.1s)
└─ 汇总总结: 12.2s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
