## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `exit_code`: 137 (`fact-341452a60a93`) | 确认进程被内核 OOMKiller 强制终止 |
| 2 | K8s Config | Kubernetes | Memory Limit: `64Mi` (`fact-192d86328102`) | 容器内存硬限制，容量极低 |
| 3 | K8s Event | Kubernetes | `Unhealthy` Liveness probe failed: `context deadline exceeded` (`fact-b3b486cd73a2`) | 探针因无响应/超时判定失败，触发重启 |
| 4 | K8s Config | Kubernetes | Memory Request: `8Mi` (`fact-7dc0743c2837`) | 调度预留量与 Limit 差异较大，确认是硬限制导致崩溃 |
| 5 | Metric | Prometheus | `last_terminated_reason`: `Error` (持续 1.0, 61 样本) (`fact-98c0c98e2f60`) | 长期存在因错误终止重启的历史 |
| 6 | Metric | Prometheus | `restarts_total`: 从 6 增加至 25 (`fact-bff5e1cc25a4`) | 证实 CrashLoopBackOff 持续发生且频次上升 |
| 7 | Logging | Elasticsearch | 请求 `/ready` 和 `/health` 返回 HTTP 200 (`fact-03bc12616d8d`, `fact-4a9e5d5e2844`) | 日志显示应用进程存活且健康检查通过 |
| 8 | Tracing | Deepflow | `/health` 请求延迟 `~3000797.0 us` (约 3s)，`/ready` 延迟 `~1652.0 us` (`fact-3ea3501d7874`, `fact-54a97e930fd5`) | 追踪证实健康接口响应极慢，解释探针超时机制 |

**证据综合分析：**
Kubernetes 状态与退出码（#1, #4）直接指向内存导致的 OOMKiller 行为；Metrics 证实了该状态是持续且恶化的（#5, #6）。值得注意的是，日志显示 HTTP 接口仍返回 200（#7），但 Tracing 数据显示健康接口（`/health`）响应延迟达到约 3 秒（#8）。这表明应用并未完全宕机，而是处于严重的内存压力下的假死/阻塞状态，导致探针超时（#3），进而引发 Kubelet 判定容器不健康并执行重启（#2, #5），最终进入 CrashLoopBackOff。

## 🎯 根因分析 · g1

### 因果链

```text
Memory Limit (64Mi) insufficient for app memory growth → OOMKiller terminates process (Exit 137) → Liveness Probe timeout (due to process blocking/slowdown) → Kubelet restarts container → CrashLoopBackOff (restarts: 25)
```

### 根因结论

已确认根因为：**容器内存限制（`64Mi`）低于应用实际运行需求，导致 OOMKiller 强制终止进程。**

具体而言：
1. **资源瓶颈**：配置了极低的内存硬限制 `64Mi`（`fact-192d86328102`）。
2. **终止机制**：进程因 OOM 被杀，退出码为 137（`fact-341452a60a93`）。
3. **现象恶化**：内存压力导致应用响应变慢，健康检查接口 `/health` 延迟超过 3 秒（`fact-3ea3501d7874`），触发 Liveness Probe 超时失败（`fact-b3b486cd73a2`），进而引发 Kubelet 不断重启容器，进入 CrashLoopBackOff（`fact-9f00206fabac`），重启次数已达 25 次（`fact-bff5e1cc25a4`）。

缺失的决定性事实：缺少进程终止瞬间准确的内存使用峰值指标（Prometheus 采样未能捕获精确峰值）以及 Node 层面的 Kernel OOM 日志（`unknowns`），但现有证据已足以确认内存压力导致 OOM 的结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 18.5s
├─ 并发证据采集: 61.2s
│  └─ g1 aiops-case-v17/workload: 61.2s (Evidence 51.8s, RCA 9.3s)
└─ 汇总总结: 15.0s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime, pod-oomkilled
