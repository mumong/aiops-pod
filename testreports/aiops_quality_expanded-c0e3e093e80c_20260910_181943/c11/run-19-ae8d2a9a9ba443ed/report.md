## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod 'aiops-case-11/workload' 被配置了自定义 finalizer 'aiops.lab/hold'，导致在容器终止后（Exit Code 137），Kubernetes 因该 finalizer 未被上游控制器释放而持续阻塞删除操作，使 Pod 处于 Terminating Stuck 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubectl` | `pod.phase: Running`, `pod.status: Terminating (lasts 30m)` | 确认 Pod 处于停滞删除状态，已持续 30 分钟 |
| 2 | K8s State | `kubectl` | `exit_code: 137`, `container.last_terminated_reason: Error` | 表明容器因 OOMKilled (Signal 137) 终止 |
| 3 | K8s Config | `kubectl` | `resource_limit.memory: 96Mi`, `resource_request.memory: 24Mi` | 提供了导致 OOM 的内存配置硬限制 |
| 4 | K8s Event | `kubelet` | `Normal Killing 30m kubelet Stopping container app` | 证明 kubelet 在 30 分钟前已成功下发停止容器指令 |
| 5 | Metric | `prometheus` | `kube_pod_container_status_restarts_total: 0` | 排除重启风暴，确认是单次终止未恢复 |

## 🎯 根因分析 · g1

```text
异常最终izers 'aiops.lab/hold' 阻塞清理 → K8s 无法彻底回收资源对象 → Pod 状态卡死在 Terminating → 用户可见资源无法释放/删除
```

**已确认的根因：** Pod `aiops-case-11/workload` 处于 Terminating Stuck 状态。根本原因是该 Pod 配置了自定义 finalizer `aiops.lab/hold`。虽然容器 `app` 已因内存限制（Exit Code 137）被 kubelet 终止并清理（见证据 #4），但由于持有该 finalizer 的外部控制器未释放它，Kubernetes 无法完成资源的最终删除操作。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 15.8s
├─ 并发证据采集: 86.5s
│  └─ g1 aiops-case-11/workload: 86.5s (Evidence 78.7s, RCA 7.7s)
└─ 汇总总结: 6.5s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
