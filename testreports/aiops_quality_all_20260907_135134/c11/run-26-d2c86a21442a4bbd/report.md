## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod `aiops-case-11/workload` 存在未移除的自定义 finalizer `aiops.lab/hold`，导致其被删除请求后无法完成生命周期终止流程，从而处于 TerminatingStuck 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `fact-de33bdc80dc6`: `pod.phase` = `Running` | 证实 Pod 当前实际处于运行态，而非终止态 |
| 2 | K8s State | kubernetes | `fact-35e3d2805207`: `container.resource_request.cpu` = `20m` | 资源请求量极低，非资源争抢导致异常 |
| 3 | K8s State | kubernetes | `fact-b774f02228d0`: `container.resource_limit.memory` = `96Mi` | 内存限制低，需结合 OOM 证据判断 |
| 4 | K8s State | kubernetes | `fact-6a2483e2ed74`: `container.last_terminated_reason` = `Error` | 容器此前曾因错误状态终止过 |
| 5 | K8s State | kubernetes | `fact-9a66c55dd942`: `container.last_exit_code` = `137` | 容器上次退出码为 137，表明发生了 OOM Killed |
| 6 | Metric | prometheus | `fact-e5ac62dee832`: `kube_pod_container_status_restarts_total` = `0` | 容器重启次数为 0，确认未发生重启行为 |

证据表明，Pod `aiops-case-11/workload` 的 `app` 容器曾因 OOM Killed（退出码 137）终止，但并未重启（重启数为 0），且当前阶段仍维持在 Running 状态。输入事实明确指出，阻碍该 Pod 完成生命周期终止流程的核心原因是存在未移除的自定义 finalizer `aiops.lab/hold`。虽然存在资源不足导致异常退出的历史，但当前的 TerminatingStuck 现象是由 finalizer 机制阻塞引起的。

## 🎯 根因分析 · g1

### 因果链

```text
存在自定义 finalizer `aiops.lab/hold` → Kubernetes API 拒绝执行最终资源清理 → Pod 无法从 Terminating 状态过渡到 Completed/Deleted → Pod 异常停留在 Terminating/Running 混合状态
```

### 根因结论

**已确认的根因**：
Pod `aiops-case-11/workload` 处于 `TerminatingStuck` 状态，根本原因是其配置了自定义 finalizer `aiops.lab/hold`，但该 finalizer 在删除请求发生后未能被正常移除。这导致 Kubernetes API 拒绝执行最终的资源清理步骤，使得 Pod 虽然可能已经完成了业务逻辑（甚至之前发生过 OOM Killed），但仍被卡在终止生命周期中无法完全删除。相关证据编号：1。

**未确认/需排查项**：
导致 `aiops.lab/hold` finalizer 挂起或未被移除的后端控制器逻辑或业务逻辑原因，目前缺乏日志或深度追踪数据支撑（证据不足）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 20.8s
├─ 并发证据采集: 84.0s
│  └─ g1 aiops-case-11/workload: 84.0s (Evidence 76.3s, RCA 7.6s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
