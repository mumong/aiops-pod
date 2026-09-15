## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态且无法删除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-11/workload` phase=Running, ContainersReady=False, message=containers with unready status: [app] | 证实 Pod 虽处于运行阶段但容器状态异常，无法对外提供服务 |
| 2 | K8s State | Kubernetes | container `app` 退出码 exit_code=137, 终止原因 reason=Error | 证实容器进程已异常终止，排除应用正常退出可能 |
| 3 | K8s State | Kubernetes | container `app` restart_count=0, 终止原因 reason=Error | 表明容器仅终止过一次且未发生重启，当前处于终态等待清理 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total{container="app"}` 当前值为 0 | 辅助印证容器未发生重启循环，排除了高频重启导致的 CrashLoopBackOff |

**证据互证说明：**
K8s 状态显示容器以退出码 137 终止（通常由 OOMKilled 引起），但 Prometheus 监控证实重启次数为 0。这确认了容器处于单次异常退出后的静默期。结合输入提供的正式 RCA，容器终止后，Kubernetes 试图回收资源，但因底层对象被自定义 `finalizer` 锁定，导致整个删除流程被阻塞。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 被删除操作触发 → 自定义 finalizer 'aiops.lab/hold' 阻止对象从 API Server 移除 → Pod 对象挂起 Terminating 状态 → 资源无法回收
```

### 根因结论

已确认根因为：Pod 存在未清理的自定义 finalizer `aiops.lab/hold`，导致 API Server 在设置 `deletionTimestamp` 后挂起删除流程。

- **机制分析**：当 Kubernetes 尝试删除 Pod 时，自定义 `finalizer` 阻止对象从 API Server 列表中移除。尽管底层容器进程已因异常（Exit Code 137）退出并停止运行，但控制平面认为删除尚未完成，从而将 Pod 对象长期维持在 Terminating 状态（证据：`phase=Running` 但 `ContainersReady=False` 且 `restart_count=0`）。
- **未知项说明**：现有证据未能提供关于该 `finalizer` 控制器本身状态的信息，也未查明触发容器退出码 137（通常为内存超限）的根本原因，但这不影响“资源无法回收”这一直接现象的定责。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 36.8s
├─ 并发证据采集: 36.2s
│  └─ g1 aiops-case-11/workload: 36.2s (Evidence 28.1s, RCA 8.0s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
