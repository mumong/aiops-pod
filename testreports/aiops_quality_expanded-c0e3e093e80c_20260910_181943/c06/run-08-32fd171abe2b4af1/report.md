## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod workload-7679bcf76-n5vp8 处于 CrashLoopBackOff 状态，容器进程以 exitCode=2 异常退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `CrashLoopBackOff` (app) | 确认容器目前处于因反复启动失败而被暂停重启的状态 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason`: `Error`, `exit_code`: 2 (app) | 确认容器最近一次异常退出的直接代码为 2 |
| 3 | K8s Event | Kubernetes | `BackOff`: `Back-off restarting failed container app` (89次) | 确认 Kubernetes 因重启失败触发了指数级退避机制 |
| 4 | K8s Config | Kubernetes | `resource_limit.memory`: `96Mi` | 提供容器内存硬限制上下文 |
| 5 | Logging | Elasticsearch | HTTP 500 错误模式: `runtime process exiting` (path: `/work`, 3次) | 证明应用在处理请求时发生内部错误并主动终止进程，与 exitCode=2 现象一致 |
| 6 | Tracing | Deepflow | HTTP Flow `GET /work` 响应 500 (dst_ip: 172.16.104.6) | 在网络层面观测到针对该 Pod IP 的相同 500 错误响应，佐证应用层故障 |

**证据关联说明：**
K8s 状态（#1, #2, #3）表明 Pod 处于崩溃循环，且退出码为 2。日志（#5）提供了具体的业务逻辑断点，指出进程是在处理 `/work` 路径并返回 500 错误时终止的。Tracing 数据（#6）独立确认了 Pod IP 172.16.104.6 确实对外输出了 500 响应，排除了网络层返回错误的可能。

## 🎯 根因分析 · g1

### 因果链

```text
应用未捕获的运行时错误 (HTTP 500) → 进程以 exitCode=2 异常终止 → Kubernetes 触发重启策略并遭遇连续失败 → Pod 进入 CrashLoopBackOff (Ready=False)
```

### 根因结论

**已确认根因：** Pod `workload-7679bcf76-n5vp8` 处于 `CrashLoopBackOff` 状态的根本原因是应用容器进程在终止时返回了非零退出码 (`exitCode=2`)。日志与追踪数据一致证明，该退出发生在处理 `GET /work` 请求时并伴随 HTTP 500 内部错误，属于应用层异常导致进程直接崩溃。

**证据不足与未知项：** 现有证据仅能确认进程“因错误退出”这一表象，无法确定具体的业务触发原因。
1. **缺乏详细堆栈：** 日志中缺失包含关键 `trace_id` (如 `0a2f7e93d108d5996daca00874df4884`) 的完整错误堆栈或详细上下文，无法区分是代码逻辑 Bug、配置缺失还是依赖服务不可用。
2. **未审查配置：** 关键依赖 `ConfigMap workload-code` 的内容未被审查，无法排除因挂载配置错误导致应用参数解析失败的可能性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 22.9s
├─ 并发证据采集: 56.5s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 56.5s (Evidence 43.6s, RCA 12.7s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-oomkilled, pod-crashloop-runtime
