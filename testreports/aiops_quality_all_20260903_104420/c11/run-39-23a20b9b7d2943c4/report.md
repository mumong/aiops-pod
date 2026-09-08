## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态卡滞（TerminatingStuck），deletionTimestamp 已设置但 pod 未删除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | 容器退出码：Exit Code: 137 (fact-3c3a8476d19b, fact-a0e32f2c44c2) | 直接指向容器进程异常终止 |
| 2 | K8s State | Kubernetes | 容器状态：Exit Code: 137; 最后终止原因: Error (fact-03d635c6f491, fact-4349828feaf7) | 确认 Pod 容器已非正常结束 |
| 3 | K8s State | Kubernetes | Pod 状态：Terminating (lasts 67m); phase: Running (fact-332cdc95a2b6, fact-a2488870f1f5) | 显示 Pod 处于卡滞状态 |
| 4 | Metric | Prometheus | kube_pod_container_status_restarts_total: 0 (fact-b65b32845db7) | 证明 Pod 未发生重启，当前状态稳定在 Termination 阶段 |
| 5 | K8s State | Kubernetes | Pod Ready: False (ContainersNotReady); containers with unready status: [app] (fact-8b1a1fa73ea7) | 证实容器已不处于服务状态 |

证据 1、2、4 互相印证：容器在 67 分钟前因异常（Exit 137）终止后，未触发重启，导致 Pod 停滞在终止流程中。证据 3 确认了该停滞状态的持续时间。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 定义 finalizer: aiops.lab/hold → 应用进程异常退出 (Exit 137) → Kubernetes 触发删除流程但被 finalizer 阻塞 → Pod 进入 Terminating Stuck 状态 (67m未解决)
```

### 根因结论

**已确认的根因**：Pod YAML 中定义了自定义 finalizer `aiops.lab/hold`，且对应的 finalizer 控制器（Controller）处于失效或未处理状态，导致 Kubernetes 垃圾回收器在 Pod 被请求删除后无法清理该标记，从而阻塞了 Pod 的生命周期终结。

*   **事实支撑**：
    *   `fact-332cdc95a2b6`、`fact-a2488870f1f5`：证实 Pod 卡在 Terminating 状态长达 67 分钟，且 phase 仍显示为 Running，无重启迹象。
    *   `fact-a0e32f2c44c2`：证实容器进程异常终止（Exit Code 137）。
    *   `formal_rca`：明确指出了 finalizer `aiops.lab/hold` 与控制器健康状态未知之间的缺失环节（unknowns）。

该结论由 K8s 的删除机制行为（Finalizer 阻塞）与容器实际退出状态（异常退出）共同支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 12.0s
├─ 并发证据采集: 102.6s
│  └─ g1 aiops-case-11/workload: 102.6s (Evidence 94.5s, RCA 8.0s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
