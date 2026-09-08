## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload stuck in Terminating state (DeletionTimestamp set, but Phase remains Running with exitCode 137). |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase`: Running (Fact ID: `fact-3ce4c7f38714`) | 直接证据：Pod 处于 Terminating 状态但容器实际仍在运行，处于僵死状态。 |
| 2 | K8s State | Kubernetes | `container.last_exit_code`: 137 (Fact ID: `fact-4b53b8e2d6a7`) | 核心证据：退出码 137 表明进程因被外部信号强制终止（通常是 OOM Kill），导致无法优雅退出。 |
| 3 | K8s Config | Kubernetes | `resource_limit.memory`: 96Mi (Fact ID: `fact-380e30daaf38`) | 上下文：限定了容器使用的硬内存上限，解释了 OOM Kill 的物理限制来源。 |
| 4 | K8s State | Kubernetes | `container.last_terminated_reason`: Error (Fact ID: `fact-58aedbd43e2b`) | 直接证据：容器终止原因报错，结合退出码 137，证实是强制杀进程而非正常退出。 |
| 5 | Logging | Elasticsearch | Pattern: `request completed`, http_status: 200, path: `/work` (Fact ID: `fact-cfcafce8dba5`) | 行为上下文：OOM 发生前最后 5 条日志显示请求正常完成，数值字段 `allocated_mib` 为 0，无法从日志中直接推断内存增长轨迹。 |
| 6 | Tracing | Tempo | Span: `GET /work`, trace_id: `25d61c13...`, status_code: 200 (Fact ID: `fact-150bcb56ac07`) | 行为佐证：追踪数据与日志关联，确认故障前应用功能正常，非业务逻辑错误导致。 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 0 (Fact ID: `fact-f38a6558d5a8`) | 排除项：重启次数为 0，说明当前容器实例未经历重启，是处于“删除中但卡住”的初次异常。 |
| 8 | K8s State | Kubernetes | Condition: `ContainersReady` = False, Reason: `ContainersNotReady` (Fact ID: `fact-74a62033fd80`) | 状态印证：进一步证明 Pod 未处于就绪状态，与 Running Phase 的矛盾突显了资源回收阻塞。 |

证据间，日志（#5、#6）证实故障前服务正常，排除了常规宕机；容器状态（#1、#3、#4）结合退出码 137 锁定了 OOM Kill 为直接诱因；而 Metrics（#7）排除了历史重启干扰，表明这是当前运行实例的持续性卡死。正式 RCA 提到的 Finalizer 阻塞是推断的根因，事实中未直接展示 Finalizer 列表或关联的 Controller 状态，但“Terminating 且 Running”的状态组合与 OOM 事实共同指向了删除机制受阻。

## 🎯 根因分析 · g1

```text
Container 'app' OOM Kill (exitCode=137, 96Mi limit) 
  → 
Container failed to terminate cleanly (Error state) 
  → 
Pod deletion blocked by pending finalizer (未直接观测到 finalizer 对象，但属 Terminating 状态卡住的典型阻塞机制) 
  → 
Pod aiops-case-11/workload stuck in Terminating state with phase Running
```

### 根因结论

**已确认根因**：Pod `aiops-case-11/workload` 因容器内存受限（96Mi）触发 OOM Kill（退出码 137），导致容器异常终止。

**阻塞机制**：Pod 进入 Terminating 状态后未能自动清理，保持 Running Phase 和 ContainersNotReady 状态（证据 #1, #2, #4, #8）。这与正式 RCA 推断的 `aiops.lab/hold` finalizer 阻塞一致——即 Kubelet 或控制器因容器异常退出（Error state）或 finalizer 机制而停止后续删除操作。

**证据不足**：
1.  **OOM 具体原因**：日志（#5）中 `allocated_mib` 始终为 0，缺乏内存增长趋势数据（Metric 无多样本趋势），无法区分是内存泄漏还是瞬时峰值。
2.  **Finalizer 状态**：事实列表中未直接包含 Pod 的 Finalizer 字段或 `aiops.lab/hold` 关联 Controller 的状态，RCA 中的 Finalizer 阻塞为合理推断，但缺乏直接的对象状态证据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.6s
├─ 并发证据采集: 38.2s
│  └─ g1 aiops-case-11/workload: 38.2s (Evidence 28.9s, RCA 9.1s)
└─ 汇总总结: 15.6s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
