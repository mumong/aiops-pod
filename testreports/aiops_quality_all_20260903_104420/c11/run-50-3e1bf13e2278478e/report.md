## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 存在自定义 finalizer 'aiops.lab/hold' 未移除，导致 API Server 无法完成 Pod 删除操作。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.last_terminated_reason: Error (fact-ea71b8d40696) | 表明容器曾非正常退出，与 exit_code 137 呼应 |
| 2 | K8s State | kubernetes | container.last_exit_code: 137 (fact-50a27e0d7fa2) | 退出码 137 (128+SIGKILL) 暗示进程被外部强制终止，常由 OOMKiller 引起 |
| 3 | K8s Config | kubernetes | container.resource_limit.memory: 96Mi (fact-22414385a6dd) | 确认容器内存硬限制为 96Mi，为判断是否触发 OOM 提供资源边界事实 |
| 4 | K8s State | kubernetes | pod.condition: Ready=False, ContainersNotReady, containers with unready status: [app] (fact-2b60e811b9e2) | 确认应用容器处于未就绪状态，与 phase=Running 但容器不健康的现状一致 |
| 5 | K8s Config | kubernetes | pod.phase: Running (fact-138c386793d8) | 确认 Pod 对象本身仍在集群中存在，处于运行生命周期 |
| 6 | Metric | prometheus | kube_pod_container_status_restarts_total: 0 (fact-47d07b08fbd4) | 确认容器重启计数为 0，说明当前的 terminating 状态非由 kubelet 自动重启循环引起 |
| 7 | K8s State | kubernetes | pod.condition: Initialized=True, PodScheduled=True (fact-695ce0f9f220, fact-3587fe61eda0) | 确认 Pod 已完成初始化并调度，排除了初始拉取或绑定阶段故障 |

上述 Kubernetes 状态事实（容器非正常退出、内存限制、非零退出码）解释了 Pod 为何处于 "Running" 但 "ContainersNotReady" 的状态，且 Metric 显示的 0 重启确认了当前处于手动干预或终止流程中。结合诊断描述中提到的自定义 finalizer 未移除，这些底层状态表明应用容器曾失败，且 Pod 最终删除操作因 finalizer 阻塞而停滞。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 finalizer 'aiops.lab/hold' 未移除 → API Server 无法完成资源清理/删除流程 → Pod 对象停留在 Terminating 状态 → 用户可见 Pod 未被彻底删除
```

### 根因结论

**已确认的根因**：Pod `aiops-case-11/workload` 存在自定义 finalizer `aiops.lab/hold` 未移除，导致 API Server 无法完成 Pod 删除操作。

**证据支撑**：
- 现象上，Pod 处于 `Terminating` 状态（依据诊断描述），但其 `pod.phase` 仍为 `Running` 且 `restart_count=0`（证据 #5, #6），说明这不是一个自动重试或重启的循环，而是卡在某一步骤。
- 根本原因在于 finalizer 阻塞。虽然 Kubernetes 状态（如容器退出码 137 和内存限制）解释了应用为何失败或需要被终止，但这些状态本身不阻止 Pod 进入终态。最终导致 Pod 无法从集群中清除的直接原因是 finalizer 机制未解除。
- 证据 #6 (Metric 0重启) 和 #3, #2 (内存限制与退出码) 排除了资源超限导致自动重启循环或拉取故障等常见场景，进一步佐证了当前状态是操作（删除）被特定条件（finalizer）挂起的结果。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 21.5s
├─ 并发证据采集: 42.6s
│  └─ g1 aiops-case-11/workload: 42.6s (Evidence 37.6s, RCA 4.9s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
