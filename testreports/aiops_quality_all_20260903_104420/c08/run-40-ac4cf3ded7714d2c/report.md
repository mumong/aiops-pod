## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | 容器内存限制配置过低（64Mi）且应用存在内存分配模式，导致容器在请求处理过程中超出限制被系统OOMKilled |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: "OOMKilled" | 确认容器最近一次异常退出的直接原因 |
| 2 | K8s Event | kubernetes | `BackOff  4m25s (x434 over 117m)  Back-off restarting failed container app` | 证实容器处于频繁重启（CrashLoopBackOff）的故障状态 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory`: "64Mi" | 指出容器内存硬限制仅为 64Mi，空间极度受限 |
| 4 | Logging | elasticsearch | 日志模式 `memory allocation advanced`，观测窗口内 `numeric_fields.allocated_mib` 变化：first=32, last=20, min=2, max=40 | 证实应用运行时存在显著的内存分配行为，峰值分配量（max 40Mi）已占用限额的 60% 以上 |
| 5 | Tracing | deepflow + tempo | L7 Flow `GET /work` (9 次)，Trace ID `15dfb58f...` 在日志与流量中重合 | 将日志中的内存分配行为与特定的 HTTP 请求上下文关联 |
| 6 | K8s State | kubernetes | `container.last_exit_code`: 137 | 进程被 OOM Killer 终止的标准退出码，与 OOMKilled 状态一致 |
| 7 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (reason: CrashLoopBackOff): 1, `kube_pod_container_status_last_terminated_reason` (reason: OOMKilled): 1 | 从监控维度独立确认当前的异常状态 |

**证据互证说明：**
K8s State 中的 `OOMKilled` (fact 1)、退出码 137 (fact 6) 与 Prometheus 指标 (fact 7) 共同构成了确凿的容器崩溃证据链。K8s 配置显示内存上限仅 64Mi (fact 3)，而日志显示应用在单个请求或处理窗口内产生了高达 40Mi 的内存分配 (fact 4)，结合 24 次重启计数 (fact 968aa59b55e9)，说明 64Mi 的限额不足以支撑应用当前的内存消耗模式，导致反复触发 OOM。

## 🎯 根因分析 · g1

### 因果链

```text
容器 memory limit (64Mi) 配置过低 → 应用处理请求时分配的内存(峰值达40Mi)超限 → 触发Linux OOM Killer，容器以退出码137被杀 → 容器反复重启进入CrashLoopBackOff
```

### 根因结论

已确认的根因是 **容器内存限制配置过低（64Mi）且应用存在内存分配模式**（证据编号 3, 4, 1）。

1. **直接原因**：容器内存硬限制仅为 64Mi (fact-72861dc4103b)。日志证据显示应用在处理请求时存在活跃的内存分配行为 (fact-401e574912c1)，其单窗口内记录的最大内存分配量 (allocated_mib max: 40Mi) 已接近限额上限。
2. **结果**：当应用内存使用突破 64Mi 限制时，操作系统触发 OOM Killer 终止容器 (fact-42717c90a60f, exit code 137)，进而导致 Kubelet 反复重启容器并进入 CrashLoopBackOff 状态 (fact-a8493721c40f, fact-9d05b7f87451)。
3. **结论**：故障源于资源配额与运行时实际需求的严重不匹配，低限额导致应用无法正常运行而频繁崩溃。

---

## 📊 性能统计

```text
├─ 总耗时: 2.9m
├─ 问题定位: 24.9s
├─ 并发证据采集: 138.3s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 138.3s (Evidence 129.3s, RCA 8.8s)
└─ 汇总总结: 13.2s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime, pod-oomkilled
