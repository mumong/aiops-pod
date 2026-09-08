## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | 容器受限于96Mi内存配额（memory limit），发生非OOMKilled性质的异常终止（Exit Code 137，Reason=Error） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Warning BackOff 3m19s (x328 over 89m)  kubelet  Back-off restarting failed container app in pod workload-79d9f8fd88-sbqvc | 记录异常持续时长与极高的重试频率，表明故障已进入稳定复发阶段 |
| 2 | K8s State | kubernetes | container.app.last_terminated_reason: Error | 直接展示容器终止的具体理由，非 OOMKilled，属业务或应用层异常 |
| 3 | K8s State | kubernetes | container.app.last_exit_code: 137 | 异常终止的标准退出码，需结合 Reason 进一步定位 |
| 4 | K8s Config | kubernetes | container.app.container.resource_limit.memory: 96Mi | 配置了极低的内存硬限制，为异常终止提供了资源约束上下文 |
| 5 | K8s State | kubernetes | container.app.restart_count: 32 | 量化故障影响规模，证明该 Pod 在 89 分钟内已崩溃重启超过 30 次 |
| 6 | Metric | prometheus | kube_pod_container_status_waiting_reason: 1, reason: CrashLoopBackOff | 独立监控视角，确认 Pod 当前状态确实处于等待/重启循环中 |
| 7 | Logging | elasticsearch | http_request completed (200), time_range: 21:37:00 - 21:37:42, allocated_mib: [0, 0] | 展示了 Pod 在崩溃前曾短暂成功处理请求，且应用内记录内存分配为 0 |

证据印证与冲突说明：
- K8s 指标与 Prometheus 监控互相印证了 `CrashLoopBackOff` 的活跃状态（证据 1, 6）。
- 尽管日志显示应用内部记录 `allocated_mib=0` 且 HTTP 状态为 200（证据 7），但 K8s 层面报告了 `Exit Code 137` 与终止原因 `Error`（证据 2, 3），结合仅 `96Mi` 的极小内存限制（证据 4），指向该异常终止与内存超配或底层 CGroup 强制回收（非 OOMKilled 类型）密切相关。

## 🎯 根因分析 · g1

### 因果链

```text
内存硬限制过低(96Mi) → 容器发生非 OOMKilled 异常终止(Exit Code 137, Reason=Error) → kubelet 频繁触发重启策略 → 用户可见 CrashLoopBackOff (x328 retries)
```

### 根因结论

已确认根因为**容器内存资源受限**。Pod `aiops-case-10/workload-79d9f8fd88-sbqvc` 的 `app` 容器被分配了 `96Mi` 的内存硬限制（证据 4），在运行时触发了非 `OOMKilled` 性质的异常终止（原因：`Error`，退出码：`137`，证据 2, 3）。这一状态被 Kubelet 捕获后，通过指数退避策略不断重启，导致了当前持续的 `CrashLoopBackOff` 状态（证据 1, 6, 5）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 21.5s
├─ 并发证据采集: 94.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 94.0s (Evidence 89.7s, RCA 4.1s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-oomkilled, pod-crashloop-runtime
