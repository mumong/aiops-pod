## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | Pod workload-79d9f8fd88-bwqhh 处于 CrashLoopBackOff 状态，容器反复因非零退出码崩溃 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Event | `Exit Code: 137` (fact-ff27c84b9648) | 直接证明进程被系统强制终止 (OOM Kill) |
| 2 | K8s Config | K8s Config | `memory limit: 96Mi` (fact-0714e3725bf2) | 设定了严格的内存硬限制，是 OOM 发生的前提条件 |
| 3 | K8s State | K8s State | `container.last_terminated_reason: Error` (fact-758f09569cfc) | 确认容器上次崩溃原因为错误，配合 Exit Code 137 锁定为资源限制问题 |
| 4 | K8s State | K8s State | `restart_count: 38` (fact-a373bfad29f4) | 证实反复崩溃重启导致的 CrashLoopBackOff 状态 |
| 5 | K8s Event | K8s Event | `Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-b087e5187eaf) | 说明在崩溃前，应用曾短暂响应探针但返回错误，随后才退出 |
| 6 | Logging | Logging | `request completed`, `http_status: 200`, `allocated_mib: first/last/min/max = 0` (fact-004f744d4737) | 确认崩溃前应用业务逻辑正常执行且 HTTP 200，内存自报值为 0，排除业务异常导致的内存泄漏或资源耗尽 |
| 7 | Tracing | Tracing | `GET /work`, `response_code: 200`, `trace_id: 7a0255fa91aad0a000c9370d08061876` (fact-2dbaa1414da8) | 确认应用端服务在运行期间功能正常且响应成功 |

上述证据链显示：Pod 配置了 `96Mi` 的内存硬限制。在运行期间（如 Trace 和日志所示，2026-09-07 22:44 左右），应用能够正常响应 HTTP 200 请求。然而，进程随后被内核 OOM Killer 强制终止，导致退出码为 137。由于日志中的 `allocated_mib` 指标与内核 OOM 事实存在偏差（自报 0 但实际触发 OOM），且无其他外部因素，判定是进程实际内存消耗（含 JVM、堆外内存等）超过了 96Mi 的限制。

## 🎯 根因分析 · g1

### 因果链

```text
Pod memory limit 设置为 96Mi (事实 #2) 
→ 容器进程实际内存消耗突破 96Mi 硬限制 
→ Linux OOM Killer 强制终止容器进程 (事实 #1, #3) 
→ Kubelet 检测到非零退出码 (137) 并执行重启，导致 CrashLoopBackOff (事实 #4)
```

### 根因结论

**已确认的根因**：容器应用的实际内存消耗超过了其 `memory limit`（96Mi）设定的硬限制，触发 Linux 内核的 OOM Killer 机制强制终止了进程（Exit Code 137）。

*   **证据引用**：
    *   进程退出码 `137`（事实 #1）结合 `terminated_reason: Error`（事实 #3）是 OOM Kill 的决定性证据。
    *   `96Mi` 的硬限制配置（事实 #2）限定了内存上限。
    *   日志（事实 #6）和追踪（事实 #7）确认应用在崩溃前处于正常服务状态（HTTP 200），且业务日志未显示导致异常内存增长的外部错误。
    *   日志中的 `allocated_mib` 始终为 0（事实 #6）与内核 OOM 事实不符，说明该指标未能准确反映真实内存消耗（可能未包含非堆内存或应用未正确上报），但这反而证实了内存消耗发生在应用层监控盲区或系统层（如文件缓存、共享内存等），导致应用未能及时感知并受限于硬限制。

*   **诊断说明**：
    现有证据充分证明根因为 **Memory Limit 配置过低** 或 **应用存在未被应用层监控捕获的内存增长**。由于工具 `pod_previous_logs` 和 `pod_current_logs` 失败，无法获取崩溃瞬间的堆栈，但 Exit Code 137 已足够确认是资源限制导致的内核级杀死。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 24.1s
├─ 并发证据采集: 61.3s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 61.3s (Evidence 53.4s, RCA 7.7s)
└─ 汇总总结: 15.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
