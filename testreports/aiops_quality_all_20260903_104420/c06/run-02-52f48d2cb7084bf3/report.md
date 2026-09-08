## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | 应用进程在处理 /work 请求时发生未捕获异常，导致进程以 Exit Code 2 主动退出，进而引发容器反复重启（CrashLoopBackOff）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason=CrashLoopBackOff`, `last_exit_code=2` (fact-1443b6aa89de, fact-11a4470ab2ff) | 直接展示容器处于反复重启失败状态，且非 OOM 或系统错误，而是应用主动退出 (Exit Code 2)。 |
| 2 | K8s State | Kubernetes | `container.resource_limit.memory=96Mi`, `container.resource_limit.cpu=200m` (fact-52c430e03430, fact-c1df05405a13) | 提供资源边界上下文；结合 Exit Code 2 可排除因硬性资源不足导致系统级崩溃的常见情况。 |
| 3 | Logging | Elasticsearch | HTTP 500 错误日志：`http_status: 500, path: /work, message: "runtime process exiting"`，时间窗 11:54-11:56 (fact-778e3ba9615a) | 确认应用在处理 `/work` 接口时捕获到严重异常，主动记录错误并退出进程。 |
| 4 | Tracing | Tempo/Deepflow | Span 记录：`HTTP GET /work` 响应 `500`，关联 `aiops.observed_mode: runtime_exit` (fact-0e0f57ddc22d)；L7 Flow 验证了 3 次 500 错误响应，与日志时间吻合 (fact-17343f705124) | 从流量维度独立证实了 `/work` 请求返回 500 导致应用侧终止行为的因果关系。 |
| 5 | K8s Event | Kubernetes | `Warning BackOff ... Back-off restarting failed container app in pod ...` 重复发生 (fact-432e7c674b94) | 确认 Kubernetes 已检测到容器异常退出，并正在执行指数退避重启策略。 |

**证据印证与冲突说明：**
1. **Kubernetes 与日志/链路完全闭环**：K8s 的 `Exit Code 2`（证据 #1）直接对应日志中的 `"runtime process exiting"`（证据 #3）以及 Trace 中的 `runtime_exit` 模式（证据 #4）。这证实了进程是“因业务异常主动退出”，而非外部资源限制或平台故障。
2. **多维观测同一故障触发点**：K8s Events（证据 #5）、日志（证据 #3）和流量（证据 #4）均一致指向 `GET /work` 请求处理失败。尽管存在部分成功请求（200），但失败路径的确定性导致了进程终止和后续的 CrashLoopBackOff。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码在处理 /work 端点时发生异常 → 进程记录 HTTP 500 并执行 sys.exit(2) 主动退出 → K8s 检测到容器非正常退出并触发重启策略 → 容器因持续失败进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认的根因**：
异常组 `g1` 的根本原因是**应用进程自身在处理 `/work` 请求时发生未捕获异常**，导致进程以 `Exit Code 2` 主动终止。
1. **故障发生机制**：日志记录表明，应用在处理 `/work` 时捕获到致命错误，记录了 HTTP 500 状态码并输出 `"runtime process exiting"`（证据 #3）；流量数据独立确认了这些请求返回 500（证据 #4）。
2. **状态维持机制**：Kubernetes 监控到容器非正常退出（`last_exit_code=2`，证据 #1），触发了标准的重启策略。由于代码中的逻辑缺陷未被修复，进程在重启后再次崩溃，进而进入 `CrashLoopBackOff` 状态（证据 #1, #5）。

**未确认因素**：
具体引发 `/work` 请求返回 500 的底层业务逻辑缺陷或 Python 异常堆栈，在现有日志输出中未被完整捕获（unknowns），因此无法进一步细化根因的具体代码行，但已充分证实“进程主动异常退出导致重启”这一核心故障链路。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 25.1s
├─ 并发证据采集: 101.5s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 101.5s (Evidence 92.0s, RCA 9.2s)
└─ 汇总总结: 14.7s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
