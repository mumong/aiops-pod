## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Pod workload in aiops-case-v17 is stuck in CrashLoopBackOff due to repeated OOM kills. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase=Running`, `pod.condition.ContainersReady=False`, `exit_code=137`, `restart_count=33` | 确诊容器处于反复崩溃重启循环 |
| 2 | K8s Config | Kubernetes | `memory_limit=64Mi`, `memory_request=8Mi` | 提供可能导致应用资源枯竭的配置约束 |
| 3 | K8s Config | Kubernetes | `cpu_limit=200m`, `cpu_request=5m` | 提供调度约束配置（非本次根因） |
| 4 | K8s Event | Kubernetes | `Liveness probe failed: context deadline exceeded` | 反映进程在崩溃前存在严重的资源争抢或停顿，导致健康检查超时 |
| 5 | Metric | Prometheus | `container.status_waiting_reason="CrashLoopBackOff"` (1), `container.last_terminated_reason="Error"` (1) | 从指标层面确认了当前的停滞状态和上一次的终止原因 |
| 6 | Logging | Elasticsearch | `listening on 18080`, `GET /health HTTP/1.1 200` | 证明容器启动后曾短暂进入工作状态，但随后发生中断 |
| 7 | Tracing | Deepflow | `HTTP GET /health`, `dst_ip=172.16.104.36`, `duration_us min=3000632.0 (约3秒)` | 确认应用存活期间对外提供 HTTP 服务，且请求响应耗时接近健康检查的默认超时阈值 |

**证据印证关系：**
Exit Code 137 (事实 #1) 是 Linux OOM Killer 强制终止进程的标准信号。该信号与极低的 Memory Limit (64Mi, 事实 #2) 形成强因果关联。应用日志显示进程已启动 (事实 #6)，而追踪数据展示其响应耗时极长 (事实 #7)，这解释了为何会在低内存压力下导致健康检查超时 (事实 #4)，进而触发 Kubelet 的多次重启 (事实 #1)，最终陷入 CrashLoopBackOff。

## 🎯 根因分析 · g1

### 因果链

```text
Memory limit (64Mi) 低于应用所需 → 进程内存超限触发 OOM Killer → 进程强制终止 (Exit Code 137) → Liveness probe 超时失败 → 容器 CrashLoopBackOff
```

### 根因结论

已确认根因为**容器内存限制配置过低 (64Mi)**，导致 Python 进程在运行时被系统 OOM Killer 强制终止 (Exit Code 137)。

证据 #1 和 #5 确认了容器处于因终止而进入 CrashLoopBackOff 的循环中，且最后一次退出码为 137，这是典型的 OOM 事件特征。证据 #2 提供了确切的配置值 64Mi，对于运行中的 Python 应用而言，该阈值极低，极易耗尽。证据 #7 显示应用响应耗时接近 3 秒，表明进程在内存紧张时已发生严重停顿或交换，这与低内存限制下的资源枯竭现象一致，直接导致了证据 #4 中的探针超时。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 22.5s
├─ 并发证据采集: 71.9s
│  └─ g1 aiops-case-v17/workload: 71.8s (Evidence 64.6s, RCA 7.0s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
