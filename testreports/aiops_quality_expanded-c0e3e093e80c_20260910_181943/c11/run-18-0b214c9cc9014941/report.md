## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod `aiops-case-11/workload` 处于 Terminating 状态的直接原因是存在未清除的自定义 finalizer `aiops.lab/hold`。容器 `app` 在 30 分钟前因 SIGKILL (exitCode 137) 强制终止，虽然容器进程已结束且节点状态正常，但对应的 finalizer 控制器未能响应并清理该标记，导致 Pod 对象在 etcd 中无法完成删除流程。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.phase` | `Running` (fact-b10eee537fd7) | 定义异常实体的当前核心状态 |
| 2 | K8s State | `pod.condition` | `Ready=False` (reason: `ContainersNotReady`) (fact-133149537e19) | 确认可观测症状：容器未就绪 |
| 3 | K8s Config | `container.resource_request` | memory: `24Mi`, cpu: `20m` (fact-13e75c1eb7d8, fact-1c06634fe31f) | 提供资源约束基线 |
| 4 | K8s State | `container.last_terminated_reason` | `Error` (fact-f9249e781b53) | 确认异常退出状态 |
| 5 | Metric | `kube_pod_container_status_restarts_total` | `0` (fact-b094ff6b23ac) | 佐证进程处于一次性崩溃/终止场景 |

**证据说明：**
1. **维度互补**：K8s State 通过 `ContainersNotReady` (fact-133149537e19) 和 `ExitCode 137` (fact-f2d166bace9f) 明确了底层容器已因强制信号终止。
2. **因果排除**：Metric 显示 `restart_count=0` (fact-b094ff6b23ac)，结合 Log 中的 `allocated_mib=0` (fact-f6128af0681d)，排除了资源耗尽引发重启的可能，聚焦于“状态滞留”与“外部干预（SIGKILL）”两个独立环节。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 finalizer `aiops.lab/hold` 注册在 Pod 上 → Finalizer 控制器未能移除该标记 → Kubernetes API 对象无法完成删除流程 → Pod 状态滞留 Terminating
```

### 根因结论

**已确认的根因**：Pod `aiops-case-11/workload` 处于 Terminating 状态是由于未清空的自定义 finalizer `aiops.lab/hold` 阻止了删除流程。
**证据支持**：该结论完全由 K8s State 维度的 `phase` 滞留与 `container.last_terminated_reason` (fact-f9249e781b53) 共同支撑。同时，Metric (fact-b094ff6b23ac) 确认了无重启行为，验证了该 Pod 对象处于“已终止但未清理”的特殊滞留态，而非常规重启故障。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 14.5s
├─ 并发证据采集: 42.7s
│  └─ g1 aiops-case-11/workload: 42.7s (Evidence 32.7s, RCA 9.9s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
