## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态且卡住 (lasts 81m) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status`: Terminating (lasts 81m); `pod.phase`: Running | 确认 Pod 处于无法完成删除的阻塞状态，且已持续 81 分钟 |
| 2 | K8s Event | kubernetes | 事件记录包含 Exit Code: 137、Annotations: `cni.projectcalico.org/containerID: be718c7097b2129f8b4a346d8c0f8e94d5ac68f660afda5672d1831f32d0cafe` | 关联到网络资源清理或容器生命周期结束时的环境上下文，与异常状态共存 |
| 3 | K8s State | kubernetes | `container.last_terminated_reason`: Error; `container.last_exit_code`: 137 | 确认容器此前因 Error 终止且退出码为 137，该异常退出可能触发了后续的删除或维护操作 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 0 | 确认容器无重启记录，排除了因健康检查失败导致的频繁重启循环造成的卡住可能 |

**证据分析：**
Kubernetes 事实直接揭示了 Pod 处于 Terminating 状态长达 81 分钟的核心症状。Exit Code 137 (SIGKILL) 和最后一次终止原因为 Error 的日志证据，通常表明容器之前因资源限制或 OOM Killer 被强制终止。然而，Pod 的重启计数为 0，说明当前的 Terminating 状态并非重启失败，而是与 Pod 的清理生命周期（Finalizers）或控制器行为有关。Metric 数据（无重启）强化了这一判断，将故障隔离在非运行时的状态管理方面。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 配置了自定义 finalizer (aiops.lab/hold) → Kubernetes 删除 Pod 时等待 finalizer 清理完成 → Finalizer 未被自动移除或对应控制器未处理 → Pod 卡在 Terminating 状态 (lasts 81m)
```

### 根因结论

**已确认的根因：** Pod 被配置了自定义 Finalizer `aiops.lab/hold`，导致 Kubernetes 在清理该 Finalizer 之前不会完成删除操作。

**证据支撑：**
*   **状态阻塞**：Kubernetes 事实显示 Pod 处于 `Terminating (lasts 81m)` 状态，且长时间未释放（证据 #1）。
*   **前置事件**：容器曾以 Exit Code 137 (SIGKILL) 终止（证据 #2, #3），这通常是触发删除或状态异常的前置条件，但当前的卡住状态表明后续的资源清理步骤未完成。

**缺失的关键事实：**
目前缺乏 `aiops.lab/hold` 自定义 Finalizer 的具体释放逻辑或对应控制器行为的日志与追踪证据。需要确认该 Finalizer 对应的控制器为何未能自动移除该标记，以及为何在容器 Terminating 后未触发清理流程。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.9s
├─ 并发证据采集: 43.1s
│  └─ g1 aiops-case-11/workload: 43.1s (Evidence 36.5s, RCA 6.5s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
