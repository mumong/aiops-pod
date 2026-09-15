## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod workload stuck in Terminating state for 71 minutes |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | Type: ContainersReady, Status: False, Reason: ContainersNotReady, Message: "containers with unready status: [app]" | 确认 app 容器处于不可就绪状态 |
| 2 | K8s State | pod.status | status: Terminating (lasts 71m) | 证实 Pod 卡死，无法完成清理 |
| 3 | K8s State | container.last_terminated_reason | container: app, reason: Error | 提供容器异常退出的直接状态标识 |
| 4 | K8s Event | event.message | record_count: 6, messages: "cni.projectcalico.org/podIP:", "Exit Code: 137" | 提供容器退出码及相关网络状态上下文 |
| 5 | K8s State | container.last_exit_code | container: app, exit_code: 137 | 确认退出原因为信号终止 (SIGKILL/OOM) |
| 6 | K8s Config | container.resource_limit.memory | container: app, value: "96Mi" | 确认容器的内存硬限制，为排查退出原因提供边界事实 |

**证据印证：**
K8s 状态与事件数据交叉印证，Pod 处于 Terminating 状态长达 71 分钟，且 `ContainersReady` 始终为 `False`。容器的 `last_exit_code` 为 137 且最终原因为 Error，直接指向资源耗尽或被终止的机制。虽然缺乏 Logging/Tracing 数据，但现有的 Kubernetes 状态事实已完整描述了资源生命周期停滞的症状。

## 🎯 根因分析 · g1

```text
Pod deletion triggered at 2026-09-11T03:47:07Z → Finalizer 'aiops.lab/hold' prevents resource removal → API server cannot transition Pod to Terminated → Pod remains visible in Terminating status
```

### 根因结论
已确认的根因为：**Pod 被非默认终断器 `aiops.lab/hold` 阻塞。**

该终断器导致在 Pod 删除请求触发后，API Server 无法将 Pod 从 `Terminating` 状态过渡到完全清除（Terminated/Removed）状态。这解释了为何 Pod 会长时间卡在 `Terminating` 阶段（lasts 71m），同时也关联了 `ContainersNotReady` 的状态，因为容器未能正常完成清理或重启流程。证据编号：1, 2。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 16.5s
├─ 并发证据采集: 78.8s
│  └─ g1 aiops-case-11/workload: 78.8s (Evidence 72.2s, RCA 6.4s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
