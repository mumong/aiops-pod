## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | 容器应用内存分配持续增长并触及 64Mi 硬限制导致 OOMKilled |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: OOMKilled`, `exit_code: 137` (fact-4963259fba7d) | 直接终止原因 |
| 2 | K8s Config | Kubernetes | `container.resource_limit.memory: 64Mi` (fact-8baa70e9e3cd) | 触发 OOM 的硬边界 |
| 3 | K8s Event | Kubernetes | `BackOff` 警告，指出重启失败 (fact-c40e1c0f9e31) | 确认可见故障现象 |
| 4 | Metric | Prometheus | `container_memory_working_set_bytes` 在 22:11:07 达到 `63852544` 字节 (60.88Mi) (fact-3c438119dd7e) | 内存使用逼近限制 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (reason: CrashLoopBackOff) (fact-4dcc5d8d6633) | 佐证当前异常状态 |
| 6 | Logging | Elasticsearch | 日志 pattern `memory allocation advanced`，`allocated_mib` 在 22:28:17 至 22:28:56 间从 10Mi 增长至 48Mi (fact-32621384f1d1) | 证明应用内部存在持续增长 |

**证据印证说明：**
*   **状态与指标一致**：K8s 报告 OOMKilled（Exit 137），同时 Prometheus 捕捉到工作集内存峰值（63.8Mi）极度逼近 64Mi 硬限制，确立了“内存超限”为终止的直接原因。
*   **现象与内部行为一致**：应用日志记录了内存分配值在 40 秒内的剧烈增长（10Mi → 48Mi），这种持续增长的行为模式解释了为何容器最终会触发硬限制并崩溃，印证了“内存分配持续增长”的诊断结论。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部内存分配持续增长 (Logging) → 工作集内存突破 64Mi 硬限制 (K8s/Metric) → OOMKilled (Exit 137) → CrashLoopBackOff 可见现象
```

### 根因结论

**已确认的根因：应用进程存在持续增长且失控的内存分配，最终触发了 64Mi 的资源硬限制。**

*   **证据编号 1-2 & 4**：K8s 状态与 Prometheus 指标共同证实，容器内存使用量已逼近并触及 64Mi 硬限制，导致内核发出 OOMKilled 信号终止容器。
*   **证据编号 6**：日志中观测到 `allocated_mib` 在短时间内连续大幅增加（从 10Mi 至 48Mi），提供了容器内发生“内存分配持续增长”的直接行为证据，支撑了根因中“持续增长”的判断。
*   **证据编号 3**：K8s BackOff 事件确认了该终止过程已导致容器进入 CrashLoopBackOff 状态，是最终的可见故障现象。

---

## 📊 性能统计

```text
├─ 总耗时: 10.3m
├─ 问题定位: 43.9s
├─ 并发证据采集: 562.0s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 562.0s (Evidence 554.0s, RCA 7.9s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime, pod-config-error
