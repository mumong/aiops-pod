## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod workload-7679bcf76-w9s9c 处于 CrashLoopBackOff 状态，容器 app 重启 12 次，退出码 2，无法就绪。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubelet/State | 容器 app 退出码 2 (fact-2b17adf1d334)；状态 CrashLoopBackOff (fact-7b2480ca8252, fact-0f3594586075) | 确诊 Pod 因应用层错误导致主动重启 |
| 2 | K8s Event | Kubelet | Warning BackOff 5m0s restarting failed container app，x155 over 39m (fact-6faa10e6dba0) | 描述 Pod 持续重启的故障现象 |
| 3 | Logging | Elasticsearch | 3 次错误日志：`runtime process exiting`，path `/work`，http_status 500 (fact-28cd7d62e7a3 等) | 捕获到进程非正常退出的关键时间点和上下文 |
| 4 | Tracing | Deepflow | 4 次 HTTP L7 Flow：`GET /work`，dst_ip 172.16.104.17，response_code 500 (fact-04e2848a7160 等) | 佐证应用在处理特定请求时发生服务器端错误并终止 |
| 5 | K8s Config | Pod Spec | 资源限制：CPU 200m, Memory 96Mi；资源请求：CPU 20m, Memory 24Mi (fact-00f701633a9c 等) | 提供排查上下文，但非当前故障的直接证据 |

**证据印证说明：**
1. K8s 状态明确显示容器因 `Error` 退出且 Exit Code 为 2，这与日志中捕获到的 `runtime process exiting` 直接对应，确认了进程因内部错误而非系统资源耗尽（如 OOMKilled 的 Exit 137）而终止。
2. Deepflow 的 L7 Flow 数据显示在请求 `GET /work` 时出现 500 状态码（fact-04e2848a7160），且其 trace_id (`491a5553286b708f2be0016438a15c3f`) 与错误日志的 trace_id 一致，证实了错误发生在特定业务请求的处理过程中。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码存在运行时错误 (触发 Exit Code 2) → Kubelet 终止容器并执行重启策略 → Pod 进入 CrashLoopBackOff 状态 → 用户请求受阻/服务不可用
```

### 根因结论

**已确认的根因**：应用程序进程在处理请求（`GET /work`）时发生运行时内部错误，导致进程以退出码 2 主动退出。Kubernetes 持续重启该容器，引发 Pod 进入 `CrashLoopBackOff` 状态。

**证据引用**：
*   **进程退出原因**：容器退出码为 2 (fact-2b17adf1d334)，且日志明确记录 `runtime process exiting` (fact-28cd7d62e7a3)。
*   **故障场景**：Tracing 显示在请求 `/work` 时发生 500 错误 (fact-04e2848a7160)，且该 Flows 的 trace_id 与错误日志一致，锁定了故障发生的请求路径。
*   **状态确认**：Pod 状态持续处于 `CrashLoopBackOff` 且处于非就绪状态 (fact-7b2480ca8252, fact-f1f8f83517c1)。

**已知局限**：
虽然已确认故障模式为“应用进程主动退出”，但导致 `runtime process exiting` 的具体应用层原因（如代码 Bug、配置错误或内部依赖失败）以及未包含 Traceback 详细堆栈的具体原因，目前证据不足，无法确认（unknowns: 缺少详细错误堆栈）。关于内存限制 (96Mi) 是否间接导致退出的问题，因退出码非 137，当前无直接证据指向 OOMKilled，但亦无法完全排除其他内存相关的边缘情况。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 25.1s
├─ 并发证据采集: 62.3s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 62.3s (Evidence 50.3s, RCA 11.7s)
└─ 汇总总结: 14.6s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
