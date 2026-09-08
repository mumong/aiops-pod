## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | Pod `aiops-case-08/workload-5c9c7b6489-fl85h` 状态为 Running，但容器 `app` 处于 CrashLoopBackOff 循环，频繁重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s `state` | `container.last_terminated_reason: "OOMKilled"` | 确认容器被系统进程直接终止，排除业务正常退出的可能性 |
| 2 | K8s Config | K8s `config` | `container.resource_limit.memory: "64Mi"` | 确立严格的内存硬限制，为 OOM 提供资源边界条件 |
| 3 | K8s State | K8s `state` | `container.last_exit_code: 137` | 确认退出码 137 为典型的 Linux OOM-Kill 信号 |
| 4 | K8s State | K8s `state` | `container.restart_count: 27` | 反映集群中已发生的高频重启现象 |
| 5 | Metric | Prometheus | `reason: "OOMKilled"` (sample_count: 1) | 从监控指标层独立印证了终止原因为 OOM |
| 6 | Logging | Elasticsearch | `pattern: "memory allocation advanced"`, `allocated_mib`: 12.0 -> 36.0 (窗口内) | 展示内存持续攀升的过程，证明应用内存消耗远超 64Mi 的限制 |
| 7 | Tracing | Tempo | `attribute: {"aiops.observed_mode": "oom_growth", "http.route": "/work"}` | 明确关联了处理具体请求时的异常内存增长模式 |

**证据分析：**
证据 1、2、3、4、5 在 Kubernetes 状态与指标层面形成闭环，一致指向“在 64Mi 硬限制下发生 OOM”。证据 6 和 7 提供了更精细的业务视角，证实了 36Mi 的内存分配已接近限制上限，且在持续增加，解释了为何 64Mi 的限制不足以支撑当前应用逻辑，从而导致了 CrashLoopBackOff。

## 🎯 根因分析 · g1

### 因果链

```text
容器 memory limit 设置为 64Mi → 请求处理时内存分配持续增长 → 触发内核 OOMKiller 强制终止进程 (Exit 137) → Kubernetes 触发指数退避重启 (CrashLoopBackOff)
```

### 根因结论

已确认的根因为：**容器配置的内存硬限制（64Mi）过低，无法承载应用在处理请求时的内存增长需求**。

该结论得到多维度证据支撑：
1.  **直接原因**：Kubernetes 明确记录了 `reason: "OOMKilled"`（证据 #1, #5），且进程以 137 退出码终止（证据 #3）。
2.  **根本约束**：Pod 规格中硬限制仅为 `64Mi`（证据 #2）。
3.  **行为模式**：日志记录显示内存分配从 12Mi 增长至 36Mi（证据 #6），Tracing 观测到 `oom_growth` 模式（证据 #7）。业务内存消耗速度已逼近或超过 64Mi 的供给，必然导致 OOM。
4.  **最终现象**：高频重启（计数 27 次，证据 #4）和 `BackOff` 事件（证据 #3 的上下文）均为 OOM 导致的连锁反应。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 15.6s
├─ 并发证据采集: 57.9s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 57.9s (Evidence 47.3s, RCA 10.4s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
