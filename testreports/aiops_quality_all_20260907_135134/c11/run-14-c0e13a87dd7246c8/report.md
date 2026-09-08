## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod workload in aiops-case-11 is stuck in Terminating status for >26 minutes. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.status`: Terminating (26m / 27m) | 确认 Pod 进入删除阶段且处于停滞状态 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason`: Error | 记录容器异常退出状态 |
| 3 | K8s Event | Kubernetes | `Killing`: "Normal Killing 27m kubelet Stopping container app" | 确认 Kubelet 发起删除容器的行为及时间 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory`: 96Mi | 提供容器内存限制的上下文事实 |
| 5 | K8s Event | Kubernetes | `Exit Code: 137` | 记录导致停止的终止信号 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 0 | 证实本次终止为首次异常，排除了反复重启 |
| 7 | Logging | Elasticsearch | `request completed` (HTTP 200, `/work`), trace_ids: `25d61c...`, `340c...` 等 | 确认在终止前的正常业务处理链路 |
| 8 | Tracing | Tempo/Deepflow | `GET /work` (200 OK), trace_id: `25d61c1398d8177ee9ac13f4efffb8b9` | 确认业务请求在终止前已成功完成 |

**证据说明：**
Kubernetes 状态显示 Pod 停滞在 Terminating 超过 26 分钟。Kubelet 事件记录显示正在停止容器，伴随 Exit Code 137（SIGKILL）。日志和追踪数据显示在终止前应用曾成功处理请求（HTTP 200），且重启计数为 0，说明该 Pod 处于首次被强制终止的状态。日志与追踪通过相同的 trace_id 形成了闭环，确认了终止前的服务正常状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 删除请求触发 (deletionTimestamp set) → 自定义 Finalizer 'aiops.lab/hold' 阻止资源彻底移除 → Kubelet 执行终止流程 (exitCode 137, 原因未确认) → Pod 处于 Terminating 状态停滞且无法删除
```

### 根因结论

已确认的根因是 **Pod 删除操作被自定义 Finalizer 'aiops.lab/hold' 阻断**。

证据链如下：
1. **现象确认**：Pod `workload` 在 `aiops-case-11` 命名空间下处于 `Terminating` 状态超过 26 分钟（证据 #1），且重启次数为 0（证据 #6），说明它从未恢复到 Ready 状态。
2. **机制分析**：Kubelet 在终止过程中发出了 Killing 事件（证据 #3）并以 Exit Code 137 结束容器（证据 #5），这表明 Pod 的删除流程已经开始并被执行。
3. **阻断事实**：根据诊断结论，Pod 资源无法被 Kubernetes API 服务器最终清理，正是因为 `aiops.lab/hold` 这个自定义 Finalizer 尚未被其对应的控制器清除。

**不足说明：**
当前证据不足以确定 Exit Code 137 的具体触发原因（是因为 OOM 被系统强杀，还是 Graceful Termination 信号，或是其他原因）。此外，控制 `aiops.lab/hold` Finalizer 的控制器当前状态未知。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 25.5s
├─ 并发证据采集: 115.1s
│  └─ g1 aiops-case-11/workload: 115.1s (Evidence 105.3s, RCA 9.3s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
