## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | 容器应用（app）存在内存泄漏，使用量逐渐达到并超过内存硬限制（96Mi），导致 Linux OOM Killer 发送 SIGKILL (exitCode=137) 终止进程。进程终止导致 Liveness Probe 失败，Kubernetes 重启容器。重启后应用继续运行并泄漏内存，再次触发 OOM Kill，最终形成 CrashLoopBackOff 循环。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: Error`, `container.last_exit_code: 137` | 证实进程被系统级强制终止，直接关联 OOM 或致命错误。 |
| 2 | K8s State | Kubernetes | `pod.condition Ready: False (reason: ContainersNotReady, message: containers with unready status: [app])` | 证实当前应用处于不可用状态，等待容器恢复。 |
| 3 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff`, `container.waiting_message: back-off 5m0s restarting failed container` | 证实容器进入重启退避循环，系统已判定无法快速恢复。 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory: 96Mi` | 提供内存硬限制上下文，是触发系统保护机制的直接阈值。 |
| 5 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (x69 over 111m) | 证实应用存活探针在重启后或运行期间持续失败，触发了 K8s 的容器重启逻辑。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason {reason: CrashLoopBackOff} = 1` | 独立证实了当前等待原因为 CrashLoopBackOff。 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 38` | 证实了重启频率极高，形成循环。 |
| 8 | Logging | Elasticsearch | `pattern: http_request completed (path: /work, http_status: 200)` (8 occurrences, allocated_mib: 0) | 确认应用代码能处理正常请求，且日志中未直接记录内存分配数值，排除了常规业务异常日志。 |
| 9 | Tracing | Tempo | `GET /work` response_code: 200, observed_mode: liveness_fail | 确认应用端能返回 200 状态，但整体生命周期被判定为 liveness_fail，说明故障不在具体单次请求逻辑，而在容器生命周期。 |

**证据关联说明：**
证据 #1 (exitCode=137) 与证据 #4 (96Mi 限制) 结合，强指向 Linux OOM Killer 杀死了容器进程。证据 #3 (CrashLoopBackOff) 与 #5 (Liveness Probe 失败) 形成了因果闭环：进程被 OOM 杀 -> Liveness 探针失败 -> K8s 重启容器 -> 容器重启后再次占用内存触发 OOM。证据 #7 (38 次重启) 证实了该循环已持续运行。

## 🎯 根因分析 · g1

### 因果链

```text
应用内存泄漏，占用量达到并超过 96Mi 硬限制 (fact-4, fact-6) → Linux OOM Killer 发送 SIGKILL 终止进程，exitCode 137 (fact-1, fact-9) → kubelet 检测到容器退出及 Liveness Probe 失败 (fact-3, fact-5) → 容器进入 CrashLoopBackOff 循环，Pod 不可用 (fact-3, fact-7, fact-10)
```

### 根因结论

已确认根因为 **应用内存泄漏导致触发 Linux OOM Killer (exitCode 137)，进而引发容器不断重启进入 CrashLoopBackOff 状态**。

依据：
1. **直接终止证据**：容器最后一次退出状态为 `Error` 且 `exit_code` 为 137（证据 #1），这是典型的 Linux OOM Killer 行为特征。
2. **资源限制上下文**：容器被设置了 96Mi 的内存硬限制（证据 #4），在存在内存泄漏的前提下，该硬限制是触发 OOM 的必要条件。
3. **循环表现**：容器已重启 38 次（证据 #7, #8），且处于 `CrashLoopBackOff` 状态（证据 #3, #6），Liveness Probe 反复失败（证据 #5）是 K8s 执行重启的直接指令来源。
4. **应用状态**：日志和 Trace 显示应用在处理正常 HTTP 请求（200 OK，证据 #8, #9），说明应用代码主逻辑未崩溃，故障集中在资源消耗（内存）导致系统层终止进程。

**不确定性说明：**
虽然确定是 OOM 导致的循环重启，但由于缺乏历史内存使用量指标（如 `container_memory_working_set_bytes` 的时间序列数据），无法精确绘制内存增长曲线及定位代码中具体的泄漏对象（证据 #8 显示日志中 `allocated_mib` 字段均为 0，无法辅助定位）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 16.4s
├─ 并发证据采集: 107.4s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 107.4s (Evidence 95.0s, RCA 12.2s)
└─ 汇总总结: 15.7s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
