## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | {'type': 'Warning', 'reason': 'BackOff', 'message': 'Warning  BackOff    2m3s (x320 over 87m)  kubelet  Back-off restarting failed container app in pod workload-79d9f8fd88-bwqhh_aiops-case-10(f2db1889-e2c8-4073-b40b-7603dc0755f7)'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (fact-18d5581945d7) | `container.waiting_reason`: CrashLoopBackOff | 确认 Pod 处于异常重启状态 |
| 2 | K8s State | kubernetes (fact-a191adc51465) | `container.last_exit_code`: 137 | 表明进程收到内核 SIGKILL 信号，疑似被 OOM Killer 终止 |
| 3 | K8s Config | kubernetes (fact-490f3c1ce7de) | `container.resource_limit.memory`: 96Mi | 确认应用存在极低的内存硬限制，为推测 OOM 提供依据 |
| 4 | K8s Event | kubernetes (fact-115bbf70876a) | `Unhealthy`: Liveness probe failed with statuscode: 500 | 确认健康检查失败是触发重启循环的直接上游原因 |
| 5 | Logging | elasticsearch (fact-221694f65584) | `pattern`: `request completed`, `http_status: 200`, `allocated_mib: 0.0` | 日志显示请求处理成功，内存分配为 0，存在正常运行的时间窗口 |
| 6 | Tracing | deepflow (fact-5d3d89ebabb0) | `flow`: GET /work 响应码 200, 耗时 10934-19270 us | 流量记录进一步证实应用在处理特定请求时未报错 |
| 7 | Metric | prometheus (fact-e60a3abb6d29) | `kube_pod_container_status_restarts_total`: 32 | 量化确认重启频率，支持长期故障推断 |

日志 (fact 5) 与追踪 (fact 6) 展示应用存在 HTTP 200 正常响应记录；然而 K8s State (fact 4) 显示 Liveness Probe 持续返回 500 并最终导致容器因 Exit 137 被杀死。正常业务日志与失败的健康检查探针之间缺乏显式 Trace_ID 关联，无法确定 Probe 失败是由应用进程崩溃（导致无响应）还是应用自身逻辑错误导致。

## 🎯 根因分析 · g1

### 因果链

```text
容器被内核 SIGKILL (Exit 137) → 导致进程异常退出 → 触发 K8s 重启策略与 Liveness Probe 失败 → 呈现 CrashLoopBackOff 现象
```

### 根因结论

现有证据不足以确认最终根因，诊断状态为 inconclusive。
1. **支持 OOM 的线索**：容器以 Exit Code 137 (SIGKILL) 退出，且内存限制仅为 96Mi (fact 2, 3)。
2. **证据冲突/空白**：虽然 Exit 137 高度暗示 OOM，但输入事实中未捕获到明确的 `OOMKilled` 容器状态或内核 OOM 日志（fact 8 显示 terminated reason 为 Error 而非 OOMKilled）。此外，日志 (fact 5) 显示存在内存分配为 0 且成功完成 HTTP 200 请求的正常记录，这与 OOM 导致的瞬间崩溃存在逻辑间隔。
3. **缺失决定性事实**：无法确认 Exit 137 是否由 Liveness Probe 失败期间的资源争用直接引发，也无法排除探针自身逻辑导致 500 响应进而被 K8s 杀死容器的可能性。缺少 `dmesg` 中的 OOM Kill 记录或探针失败时的详细应用堆栈日志。

---

## 📊 性能统计

```text
├─ 总耗时: 2.9m
├─ 问题定位: 21.7s
├─ 并发证据采集: 140.4s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 140.4s (Evidence 132.0s, RCA 8.2s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
