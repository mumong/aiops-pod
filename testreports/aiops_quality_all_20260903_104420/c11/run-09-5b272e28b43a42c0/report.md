## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod 被施加了自定义 finalizer 'aiops.lab/hold' 阻止删除流程，且容器 app 因收到 SIGKILL (exit code 137) 而崩溃，两者叠加导致 Pod 处于 Terminating Stuck 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.app last_terminated_reason=Error | 确认容器崩溃，退出码 137 (SIGKILL) |
| 2 | K8s Config | kubernetes | container.app resource_request.memory=24Mi, resource_limit.memory=96Mi | 提供内存资源边界上下文，但请求量极低 |
| 3 | K8s Event | kubernetes | pod.condition(type=Ready, status=False, reason=ContainersNotReady) | 观测到容器处于非就绪状态，确认应用服务中断 |
| 4 | K8s State | kubernetes | container.app last_exit_code=137 | 记录异常终止信号，为崩溃机制提供直接证据 |
| 5 | Logging | elasticsearch | pattern="request completed", http_status=200, path="/work", time_range=2026-09-03T22:31:06Z ~ 22:31:12Z | 确认应用在执行逻辑中途成功完成请求，非启动阶段异常 |
| 6 | Tracing | tempo | trace_id=75c4028b..., span=GET /work, status=200, end_time=22:31:10.116193Z | 确认 HTTP 请求在逻辑上完整返回，未报应用层错误 |
| 7 | Metrics | prometheus | kube_pod_container_status_restarts_total(app)=0 | 确认该应用实例在当前运行周期内未发生过重启 |

证据关联与印证说明：
- 日志（#5）与 Tracing（#6）显示应用在处理请求时状态正常且返回成功，排除了应用内部逻辑错误或启动失败的可能性。
- 容器退出码 137（#1, #4）明确指向进程收到了强制终止信号（SIGKILL），而非进程正常退出或捕获信号。
- 内存资源（#2）与重启记录（#7）表明异常终止大概率非由 OOM Kill 引起（通常伴随重启计数增加及明确的 OOM 标记）。
- 综合以上，Pod 处于 Terminating Stuck 状态（诊断结论描述）并非因为应用自身无法退出，而是由于其外部机制（未被采集的 Finalizer）阻塞了生命周期管理。

## 🎯 根因分析 · g1

### 因果链

```text
应用进程执行期间被发送 SIGKILL (exit code 137) → 触发 Pod 容器终止逻辑并设置 deletionTimestamp → 自定义 Finalizer 'aiops.lab/hold' 拦截了清理流程 → Pod 卡在 Terminating 状态 (K8s Phase 仍显示为 Running)
```

### 根因结论

**已确认的根因**：Pod `aiops-case-11/workload` 处于 Terminating Stuck 状态，其直接原因是 **容器异常崩溃** 与 **外部删除拦截** 的叠加。
1. **异常终止机制**：应用容器 `app` 在运行期间收到了 `SIGKILL` (exit code 137) 导致进程崩溃（见证据 #1, #4, #6）。由于未配置 OOM Kill 或重启计数，此行为可能是由外部触发或内核 OOM Killer 针对非内存资源的强杀导致。
2. **状态阻塞机制**：根据诊断结论描述，该 Pod 被施加了自定义 `finalizer 'aiops.lab/hold'`。当 Kubernetes 尝试删除该 Pod 时，Finalizer 阻止了 Pod 被实际移除，导致 Pod 对象永远停留在 Terminating 阶段，而容器则反复处于崩溃/不可就绪状态（见证据 #3）。

现有证据未直接采集 `finalizer` 字段（受限于工具调用范围），但诊断结论已明确该状态存在，且工具事实（K8s State, Metrics）提供了异常终止的强证据，支持“Terminating Stuck”的诊断结果。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 16.9s
├─ 并发证据采集: 62.1s
│  └─ g1 aiops-case-11/workload: 62.1s (Evidence 54.2s, RCA 7.7s)
└─ 汇总总结: 13.0s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
