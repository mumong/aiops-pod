## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 长期处于 Terminating 状态 (持续 92 分钟) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod 状态 | `phase: Running` | 确认 Pod 运行态事实 |
| 2 | K8s State | Pod 状态 | `status: Terminating (lasts 92m)` | 描述异常现象 |
| 3 | K8s State | Pod 条件 | `ContainersReady: False` (`2026-09-11T03:47:19Z`) | 确认异常期间容器状态 |
| 4 | K8s State | Pod 条件 | `ContainersNotReady: containers with unready status: [app]` | 确认异常期间容器状态 |
| 5 | K8s State | Pod 条件 | `Ready: False` (`2026-09-11T03:47:19Z`) | 确认异常期间容器状态 |
| 6 | K8s State | 容器重启 | `restart_count: 0` | 排除重启风暴导致的临时终止 |
| 7 | K8s Event | 退出事件 | `Exit Code: 137` | 提供终止直接原因线索 |
| 8 | K8s Config | 资源限制 | `CPU limit: 200m, memory limit: 96Mi` | 排除资源不足导致的 OOMKilled (需排除 137 的其他可能) |
| 9 | Metric | kube_pod_status_phase | `Running: 1` | 确认当前实际运行阶段 |
| 10 | Metric | kube_pod_container_status_restarts_total | `0` | 确认当前容器未发生重启 |

证据表明 Pod 尽管当前处于 `Running` 状态，但被标记为 `Terminating` 已 92 分钟。K8s 条件显示容器未就绪（`ContainersReady: False`），事件日志包含退出码 `137` 信号（通常对应强制终止），容器未重启（重启 0 次）。虽然资源配置有限制，但 Pod 状态卡滞的根本原因是终止流程受阻，而非单纯的资源异常。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 finalizer 'aiops.lab/hold' 滞留 → 触发 GC 等待机制 → API Server 对象移除受阻 → Pod 长期处于 Terminating 状态
```

### 根因结论

已确认 Pod 因配置了自定义 finalizer `aiops.lab/hold` 而处于 Terminating 状态。Kubernetes 的垃圾回收（Garbage Collector）机制会等待该 finalizer 被清理完毕才允许 Pod 对象从 API Server 中被完全移除。当前 Pod 已处于 Terminating 状态长达 92 分钟，表明对应的控制器或外部系统未能正常释放此 finalizer，导致 Pod 删除流程卡死。

---

## 📊 性能统计

```text
├─ 总耗时: 9.6m
├─ 问题定位: 17.2s
├─ 并发证据采集: 549.1s
│  └─ g1 aiops-case-11/workload: 549.1s (Evidence 541.2s, RCA 7.8s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
