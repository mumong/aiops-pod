## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 持有 finalizer 'aiops.lab/hold'，该外部资源清理钩子未成功执行或被无限期挂起，导致 Kubernetes API Server 无法移除该 finalizer，从而将 Pod 永久阻塞在 Terminating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Phase | `phase: Running` (fact-c9923fde4cc0) | 表明容器进程实际上在正常运行，未崩溃 |
| 2 | K8s State | Pod Status | `Terminating (lasts 74m)` (fact-3201fbbbdba8) | 显示 Pod 被强制删除后长期滞留，非正常退出流程 |
| 3 | K8s Event | Pod Conditions | `Ready: False` (ContainersNotReady) (fact-43bec56b66d1) | 确认容器虽然存活但不可用于服务请求，状态异常 |
| 4 | Metric | Restart Count | `value: 0` (fact-ae3d19226059) | 结合状态说明 Pod 从未经历正常的容器重启周期 |

现有 K8s 状态与 Metric 事实高度一致，表明该 Pod 处于“假死”状态：进程未崩溃（非 OOM/Killed），但 API Server 的删除逻辑因外部钩子阻塞，导致生命周期卡在 Terminating。

## 🎯 根因分析 · g1

### 因果链

```text
持有 finalizer 'aiops.lab/hold' → 外部清理钩子执行超时/挂起 → API Server 无法移除 finalizer → Pod 永久阻塞在 Terminating 状态
```

### 根因结论

已确认根因为 Pod `aiops-case-11/workload` 被 `aiops.lab/hold` 外部资源清理钩子无限期阻塞。事实依据显示 Pod 实际进程仍处于 `Running` 状态（fact-c9923fde4cc0），且自 Terminating 开始（lasts 74m, fact-3201fbbbdba8）以来未发生任何重启（restart_count: 0, fact-ae3d19226059）。这证实了 Pod 未因内部错误（如 OOM）退出，而是被 Kubernetes 删除流程挂起，等待外部资源清理完成。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 15.1s
├─ 并发证据采集: 73.8s
│  └─ g1 aiops-case-11/workload: 73.8s (Evidence 67.3s, RCA 6.1s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
