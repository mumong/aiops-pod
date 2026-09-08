## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod workload-7679bcf76-w9s9c 处于 CrashLoopBackOff 异常状态，容器持续非正常退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Event | `Warning BackOff ... Back-off restarting failed container app in pod workload-7679bcf76-w9s9c` | 确认 Pod 处于 `CrashLoopBackOff` 异常状态。 |
| 2 | K8s State | K8s State | `container.last_terminated_reason: Error` | 证明容器此前因 `Error` 终止，直接触发重启失败。 |
| 3 | K8s State | K8s State | `container.last_exit_code: 2` | 提供具体的错误退出码（非 0 的正常退出）。 |
| 4 | K8s Config | K8s Config | `resource_limit.memory: 96Mi` | 排除内存硬限制不足导致的 OOMKill。 |
| 5 | Logging | Elasticsearch | `http_request error ... message: "runtime process exiting", http_status: 500, path: "/work", numeric_fields.allocated_mib: 0` | 提供崩溃现场证据：应用处理 `/work` 时发生 HTTP 500 错误并主动退出；内存占用为 0，排除了资源超限。 |
| 6 | Tracing | Tempo (Span) | `GET /work` Span 结束时间 `12:27:04` 与最后日志时间 `12:27:06` 一致，确认了单次故障请求的具体路径。 | 关联了 Tracing 与 Logging，证明 `/work` 端点执行确实引发了系统级异常。 |
| 7 | Metrics | Prometheus | `kube_pod_container_status_waiting_reason ... reason: "CrashLoopBackOff"` | 独立确认 Pod 状态的等待原因为 CrashLoopBackOff。 |

**证据印证：**
1. `fact-3233a3158396`（终止原因为 Error）与 `fact-e2e0cd39ab76`（日志显示 "runtime process exiting" 及 HTTP 500）互相印证，证明容器是因内部逻辑错误崩溃，而非外部资源限制（内存仅 0 MIB）或被杀。
2. `fact-3ebc199ae404`（重启次数 12）结合 `fact-db9930f2d85b`（指标显示 CrashLoopBackOff 和 Error），确认了应用正在经历反复的非正常退出。
3. `fact-353edac45566` 与 `fact-e2e0cd39ab76` 在时间窗口和请求路径（`/work`）上高度吻合，锁定了具体的故障端点。

## 🎯 根因分析 · g1

### 因果链

```text
应用存在代码逻辑缺陷 → 处理 /work 请求时触发运行时异常并主动退出（Exit Code 2） → Kubelet 检测容器死亡并反复重启失败 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认的根因：** 应用代码逻辑缺陷。

**分析与依据：**
证据链明确指向了应用自身的运行时异常，排除了基础设施因素：
1. **故障现象锁定**：Pod 状态长期处于 `CrashLoopBackOff`，且终止原因为 `Error`，退出码为 `2`（`fact-3233a3158396`, `fact-4c36e5bb559a`）。
2. **排除资源限制**：尽管容器配置了内存硬限制 `96Mi`，但日志中记录的错误时刻内存分配量（`allocated_mib`）为 `0`（`fact-e2e0cd39ab76`），证明崩溃不是由 OOM（内存溢出）引起的。
3. **确定故障点**：
   - **日志证据**：记录到 `http_request` 级别的 `500` 错误，并伴随明确的 `runtime process exiting` 信息（`fact-e2e0cd39ab76`）。
   - **Trace 证据**：Tempo 中的 `GET /work` Span 日志确认了故障请求路径（`fact-353edac45566`）。

综上，根本原因是应用代码在处理 `/work` 接口时发生了运行时错误（导致退出码 2 和 HTTP 500），触发了 K8s 的 CrashLoop 保护机制。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 23.6s
├─ 并发证据采集: 73.9s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 73.9s (Evidence 64.2s, RCA 9.5s)
└─ 汇总总结: 14.7s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
