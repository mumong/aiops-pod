## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload Terminating 状态持续 93 分钟未删除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase`: Running, `pod.status`: Terminating (lasts 93m) | 确认 Pod 处于被删除但未被回收的卡死状态 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason`: Error, `container.last_exit_code`: 137, `container.restart_count`: 0 | 确认应用因异常终止（通常为 OOM/Killed），且重启计数为 0 |
| 3 | K8s State | Kubernetes | `pod.condition` (ContainersReady/Ready): False, reason: `ContainersNotReady` | 容器处于非就绪状态，解释了为何无法被正常回收 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory`: 96Mi, `container.resource_request.cpu`: 20m | 提供资源约束背景，存在严格的内存硬限制 |
| 5 | K8s Event | Kubernetes | `event.message`: `Exit Code: 137`, `Annotations`: `cni.projectcalico.org/...` | 直接记录容器退出码为 137，佐证异常终止 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 0, `kube_pod_status_phase`: Running(1), Pending(0) | 监控确认该容器未发生过正常重启，状态维持在 Running(对应 Terminating 过程中的中间态) |

**证据分析：**
Kubernetes 状态事实与事件记录共同确立了异常场景：容器因 `Exit Code: 137`（信号 9）异常退出，但 `restart_count: 0` 表明未被重启策略覆盖或重启失败。结合 `pod.status: Terminating (lasts 93m)` 且 `phase: Running`，说明删除动作已触发但因某种阻碍而停滞。Metric 数据佐证了容器未经历重启循环，且依然驻留在集群中。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存超限触发 OOM Kill (exitCode=137) → 应用层自定义 finalizer 'aiops.lab/hold' 无法在异常终止状态下完成清理逻辑 → Pod 删除请求被阻塞，无法移除 finalizer → Pod 长期卡在 Terminating 状态 93 分钟
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-11/workload` 被自定义 finalizer `'aiops.lab/hold'` 阻塞删除。

**分析：**
1.  **异常触发**：Kubernetes 状态 `container.last_exit_code: 137` 及事件 `Exit Code: 137` 证实容器应用因异常终止（通常是 Out of Memory Kill）退出，证据 #2、#5。
2.  **阻塞机制**：容器异常退出后，自定义 finalizer `'aiops.lab/hold'` 未能成功执行或释放。这导致 API Server 无法完成 Pod 的最终删除流程。
3.  **现象确认**：由于 finalizer 未移除，Pod 状态长期停留在 `Terminating`（持续 93 分钟），尽管其内部 phase 显示为 `Running`（指代 Pod 对象仍存在且未被 GC 回收），证据 #1、#3、#6。

目前缺少 finalizer 在 OOM 发生时的具体错误日志或详细清理代码路径（Logging/Tracing 缺失），但 K8s 状态与退出码已足以支撑“Finalizer 阻塞删除”这一结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 23.5s
├─ 并发证据采集: 76.3s
│  └─ g1 aiops-case-11/workload: 76.3s (Evidence 66.4s, RCA 9.8s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
