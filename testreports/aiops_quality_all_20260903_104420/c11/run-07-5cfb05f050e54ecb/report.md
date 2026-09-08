## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | {'container': 'app', 'reason': 'Error'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase`: Running; `deletionTimestamp` 存在 (隐含) | 确认 Pod 处于异常停滞状态，删除请求已发出但未能清理 |
| 2 | K8s Config | kubernetes | `container.resource_limit.memory`: 96Mi; `container.resource_request.memory`: 24Mi | 确认容器具有严格的内存硬限制，为分析 137 退出码提供资源上下文 |
| 3 | K8s State | kubernetes | `container.last_exit_code`: 137 | 直接证据，容器进程被强制终止（OOM 或 Kill），无法区分具体触发源 |
| 4 | K8s State | kubernetes | `pod.condition` 记录: `ContainersNotReady` (message: "containers with unready status: [app]"), `ContainersReady` 为 `False` | 确认容器最终处于不健康/未就绪状态，解释了无法通过就绪检查 |
| 5 | Logging | elasticsearch | `log.message` pattern: `request completed` (200), `/work`, `allocated_mib`: 0.0 (min/max/first/last 均为 0) | 展示终止前的最后有效业务活动，证明应用逻辑本身能完成请求 |
| 6 | Tracing | deepflow (l7_flow) | GET `/work` flow: 5 occurrences, src: `172.16.104.23`, dst: `172.16.104.23`, status: 200, `trace_ids`: 包含 `75c4...` | 跨维度印证日志记录，确认应用服务在处理业务请求 |
| 7 | Tracing | tempo (span) | GET `/work` span: `trace_id`=`75c4028b11532f074defb107fd297f49`, duration: ~3μs | 与日志 trace_id 完全一致，证明该请求在应用层快速且成功处理，无超时 |

**证据关联说明：**
- **业务层正常，系统层异常**：日志 (fact-0cc107c01331 等) 与链路数据 (fact-15e0fa925b36, fact-4ea42c1a6662 等) 均显示应用成功处理了请求（HTTP 200，无错误日志，内存指标显示为0）。这说明终止原因**不是**业务逻辑错误或常规的性能过载。
- **资源与退出码的矛盾**：虽然内存限制较低（96Mi），但日志记录的 `allocated_mib` 始终为 0，且 exitCode 137 可能是外部 Kill 或探针失败，单纯内存不足通常会有 OOMKilled 相关标记（本例中未提供 explicit OOMKilled reason，仅给了 generic Error 和 exit 137）。
- **核心阻塞点**：状态事实 (fact-9e22f894f808) 与现象（Terminating 状态）的结合，直接指向了 `aiops.lab/hold` finalizer 的阻塞作用，而非容器自身崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
finalizer 'aiops.lab/hold' 存在于 Pod spec (已知事实) 
→ Kubernetes 等待 finalizer 释放 (Kubernetes 机制) 
→ Pod deletionTimestamp 已设置，但容器仍被 Kubelet 杀除 (exit 137) (现象矛盾)
→ Pod phase 保持 Running 且不结束删除 (异常状态)
```

### 根因结论

**证据不足**。

现有证据足以确认以下**表象事实**：
1.  Pod `aiops-case-11/workload` 正处于 Terminating 阻塞状态，`deletionTimestamp` 已存在但 `pod.phase` 仍为 Running。
2.  容器 `app` 的终止代码为 137，且在终止前有成功处理的 HTTP 请求记录。

但以下**决定性事实缺失**，导致无法得出确切的根因：
1.  **Finalizer 持有者不明**：缺乏证据指出哪个 Controller、Service 或 Webhook 持有 `aiops.lab/hold` finalizer，也未发现相关的 Event（如 `AdmissionWebhook` 拒绝或 `FinalizerController` 日志）来解释为何它拒绝释放。
2.  **exitCode 137 的触发源不明**：虽然内存限制为 96Mi，但无内存飙升的 Metric 证据，且日志中内存指标为 0。无法确定 137 是 OOM Killer 触发的，还是 Liveness Probe 失败触发的，还是外部手动 `kill`。
3.  **Phase 不一致的原因不明**：Kubernetes 标准行为是在容器终止后更新 Phase 或状态。在 finalizer 存在的情况下，Pod 通常保留在 Terminating 中，但 phase 可能会更新。目前的 `Running` phase 结合 `ContainersNotReady` 状态，属于需要检查 `kubelet` 或 API Server 日志才能解释的状态异常。

建议补充采集包含 `aiops.lab/hold` finalizer 绑定的 **AdmissionWebhook** 或 **Finalizer Controller** 的日志与 Event，以及容器 **CRI 级别的退出详情**。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 19.4s
├─ 并发证据采集: 44.5s
│  └─ g1 aiops-case-11/workload: 44.5s (Evidence 33.6s, RCA 10.7s)
└─ 汇总总结: 17.6s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
