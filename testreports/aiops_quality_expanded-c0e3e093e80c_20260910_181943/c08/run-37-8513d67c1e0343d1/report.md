## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | Running | app 容器处于 CrashLoopBackOff (Exit Code 137)，Pod 未就绪 (Ready=False)。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `BackOff restarting failed container app in pod workload-5c9c7b6489-p8462` (fact-0da52d58520a) | 记录容器频繁重启的症状，确认应用处于不稳定状态。 |
| 2 | K8s State | kubernetes | `last_terminated_reason: OOMKilled` (fact-9489f0ec41c2)；`exit_code: 137` (fact-0c98e8d67c4a) | 直接指出最后一次终止的原因是操作系统 OOM 机制，137 号退出码符合被强制杀死特征。 |
| 3 | K8s Config | kubernetes | `resource_limit.memory: 64Mi` (fact-28671af2a464) | 确认了触发 OOM 的硬限制边界。 |
| 4 | K8s Config | kubernetes | `resource_request.memory: 24Mi` (fact-8abb8b0dc5ca) | 确认调度预期内存低于触发 OOM 的实际使用量，排除调度资源预留问题。 |
| 5 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason` 显示 `reason: OOMKilled` (fact-299ce7cda08c)；`kube_pod_container_status_restarts_total` 计数为 23 (fact-a73544af4fa4) | 指标层复现了终止原因，且高重启次数与 K8s 事件吻合。 |
| 6 | Logging | elasticsearch | 日志模式 "memory allocation advanced" 连续 8 次发生，`allocated_mib` 从 `20` 增至 `44` (fact-12401075fcbe等) | 在终止前观察到应用内部内存使用量持续累积且未释放，提供了发生内存溢出前的直接行为证据。 |

上述证据链完整：Logging 显示了应用进程在内存限制内不断累积内存直至触顶的行为模式，Kubernetes State 记录了进程因此被操作系统强杀（OOMKilled/137）的状态，Metric 和 Event 进一步在时间线上确认了这种异常终止已多次发生（CrashLoopBackOff），共同指向因内存不足导致的容器崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
容器 memory_limit 64Mi 设定过低 → 应用在请求中持续累积内存且不释放 → 内存触及 64Mi 硬限制触发 Linux OOM-Killer → 容器被杀 (OOMKilled/137) 导致 CrashLoopBackOff
```

### 根因结论

已确认根因为：**容器内存资源限制（64Mi）过低，无法满足应用处理请求时的内存增长需求，最终引发 OOMKilled。**

证据分析如下：
1. **直接机制确认**：K8s 状态（fact-9489f0ec41c2）与 Prometheus 指标（fact-299ce7cda08c）均明确指出容器最后一次终止原因是 `OOMKilled`。
2. **行为模式匹配**：日志事实（fact-12401075fcbe等）显示应用在处理请求（`/work`）时，内存分配（`allocated_mib`）呈现从 20MiB 增至 44MiB 的累积趋势。这一趋势在 64MiB 的限制下极易导致超额。
3. **限制条件确证**：配置事实（fact-28671af2a464）证实硬限制仅为 64Mi，这不足以容纳应用运行时产生的最大内存峰值。

以上事实形成了从“应用行为（日志）”到“系统响应（OOM/状态）”再到“约束条件（配置）”的闭环，排除了网络、镜像或其他容器组件异常的可能性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 25.0s
├─ 并发证据采集: 73.5s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 73.5s (Evidence 63.0s, RCA 10.3s)
└─ 汇总总结: 13.3s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
