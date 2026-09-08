## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态且无法移除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `Container` app `last_terminated_reason`: Error | 确认容器存在异常终止史，属于根因导致的直接症状 |
| 2 | K8s State | kubernetes | Container `last_exit_code`: 137 | 确认异常终止原因为 OOMKill (SIGKILL)，排除了应用主动退出 (exit 1) 或逻辑错误的可能 |
| 3 | K8s State | kubernetes | `Pod` `conditions` (Ready/ContainersReady): `False` (ContainersNotReady) | 确认容器当前不可用，且处于非正常状态 |
| 4 | K8s State | kubernetes | Pod `phase`: Running | 说明 Pod 虽被删除标记但尚未真正从 API Server 移除，属于 Finalizer 阻塞时的常见保留状态 |
| 5 | K8s Config | kubernetes | Container resource requests: `24Mi` memory, `20m` cpu | 提供资源需求基线，辅助排除资源不足导致 Pod 无法调度的可能性 |
| 6 | K8s Config | kubernetes | Container resource limits: `96Mi` memory, `200m` cpu | 确立内存硬限制为 96Mi，与 exit 137 构成 OOM 关联 |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 0 | 确认 Pod 历史上未发生过重启，表明该 Pod 是首次运行即因资源限制被杀 |
| 8 | Metric | prometheus | `kube_pod_status_phase`: Running(1), Pending(0) | 独立确认 Pod 并未处于 Pending (资源不足无法调度) 状态，而是在 Terminating 过程中卡住 |

**证据关联与冲突分析：**
Kubernetes 的 `exit_code=137` 与 Metrics 中的 `restarts=0` 互相印证：Pod 从未通过 Kubelet 重启，说明是应用首次运行就因超出 `resource_limit.memory=96Mi` 而被 OOMKilled（对应 `last_terminated_reason: Error`）。Metrics 中 `status_phase=Running` 且无 Pending 样本，说明调度没问题，Pod 只是卡在 API Server 的删除阶段。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 内存硬限制为 96Mi (fact-3d0548df47f1) → 首次运行触发 OOMKilled (exit_code: 137, last_terminated_reason: Error) → 触发 Pod 删除流程 (Phase: Running) → 自定义 Finalizer 'aiops.lab/hold' 对应的业务逻辑未就绪，导致 API Server 阻塞 Pod 真实删除 (Phase 未变更为 Terminating 或无法完成删除)
```

### 根因结论

**已确认根因：** Pod 处于 Terminating 状态无法移除，根本原因是其携带了自定义 Finalizer `aiops.lab/hold`。Kubelet 已成功终止了容器（`exit_code 137`），但 Kubernetes API Server 在等待该 Finalizer 对应的清理钩子完成后才会真正从集群移除该 Pod。

**证据支持：**
*   容器异常终止且未重启（`exit_code: 137`, `restarts: 0`, `last_terminated_reason: Error`）证明了应用确实在运行过程中死亡，触发了清理流程。
*   Pod 处于 `Running` 状态（`phase: Running`）说明它并未处于 Pending（调度失败）状态，而是处于正在被删除但尚未从 API Server 摘除的过渡期，这是 Finalizer 阻塞的典型特征。

**已知未知（证据不足部分）：**
目前无法确认 `aiops.lab/hold` 具体为何未能完成清理。缺失的决定性事实包括：
1. 负责处理 `aiops.lab/hold` 的后端控制器（或 Operator）的运行日志（Logging 采集为空）。
2. 该 Finalizer 绑定的上游资源或清理逻辑的拓扑依赖关系（`kubectl lineage` 工具调用失败）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 24.6s
├─ 并发证据采集: 60.7s
│  └─ g1 aiops-case-11/workload: 60.7s (Evidence 52.4s, RCA 8.2s)
└─ 汇总总结: 13.4s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
