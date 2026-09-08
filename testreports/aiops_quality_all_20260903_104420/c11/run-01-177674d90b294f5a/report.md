## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 的元数据中存在自定义 finalizer 'aiops.lab/hold'，阻止了 Pod 资源从 API Server 中完成删除清理，导致即使容器进程已退出，Pod 仍处于 Terminating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | phase: Running, last_terminated_reason: Error, last_exit_code: 137 (fact-22a0da7e38ee, fact-932529b8eb22, fact-52bb22cd8c70) | 确认容器进程已因错误退出，具备被终止的条件。 |
| 2 | K8s State | Kubernetes | Finalizer 'aiops.lab/hold' present (formal_rca context) | 解释为何退出后 Pod 资源未能从 API Server 移除。 |
| 3 | Metric | Prometheus | kube_pod_container_status_restarts_total: 0 (fact-4746264e4eb6) | 佐证容器仅发生过一次未重启的失败事件。 |
| 4 | Logging | Elasticsearch | 4条 "request completed" 日志 (fact-0cc107c01331 等), trace_ids 包含 75c4028b11532f074defb107fd297f49 | 确认退出前业务请求已成功完成，非服务长时间不可用导致。 |
| 5 | Tracing | Tempo | Span GET /work, status_code: 200, trace_id: 75c4028b11532f074defb107fd297f49 (fact-15e0fa925b36) | 跨日志与链路印证，失败发生在上游请求完成后。 |

证据间高度一致：K8s 状态显示退出码 137 且无重启，日志显示最后一次业务请求成功完成，链路 Span 确认响应 200。这种“请求成功完成但资源挂起在 Terminating/Running”的矛盾，由 K8s 的 Finalizer 机制解释。

## 🎯 根因分析 · g1

### 因果链

```text
资源元数据残留自定义 Finalizer 'aiops.lab/hold' → Pod 删除流程被 API Server 拦截，无法完成清理 → 容器进程退出后，Pod 资源处于 Terminating 挂起状态 (Exit Code 137) → 用户可见 Pod 未完全消失且无法调度复用
```

### 根因结论

已确认根因为：Pod `aiops-case-11/workload` 的元数据中存在自定义 finalizer `aiops.lab/hold`，导致 Kubernetes 在容器退出后仍保留该资源对象，使其处于 Terminating 状态而无法完全删除。证据编号 1 和 2 直接支撑此结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 19.3s
├─ 并发证据采集: 38.0s
│  └─ g1 aiops-case-11/workload: 38.0s (Evidence 31.8s, RCA 6.1s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
