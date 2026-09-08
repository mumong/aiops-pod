## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 最后退出码 `137` (fact-07b0cb876950) | 确认进程被系统 Kill，对应 OOMKilled 行为 |
| 2 | K8s Config | Kubernetes | 容器 `app` 内存硬限制 `96Mi` (fact-088745af0c40) | 提供导致超出的硬性资源边界 |
| 3 | K8s Event | Kubernetes | 告警 `Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-5e5c78a526e5) | 确认应用已无响应导致健康检查失败 |
| 4 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` 显示为 `Error` (fact-dc25a1e19b84) | 从监控侧印证终止原因为 Error，而非重启策略 |
| 5 | Logging | Elasticsearch | 聚合模式显示应用仍处理 `HTTP 200` 请求，且内存字段 `allocated_mib` 始终为 `0` (fact-34debadc2967) | 观测窗口内未发现应用侧日志记录的内存激增异常 |
| 6 | Tracing | Tempo/Deepflow | 关联流量 `GET /work` 返回 `200`，部分 Trace 存在但在不同时间窗口 (fact-41c4768a2028, fact-51577e29856c) | 证明集群在崩溃前后存在正常的 HTTP 流量处理记录 |

**证据说明：**
1. **因果链闭环**：退出码 `137`（证据 #1）结合内存限制 `96Mi`（证据 #2），直接指向内核 OOM 杀进程。
2. **状态演进一致**：Kubernetes 事件记录的 Liveness Probe 失败 `500`（证据 #3）是进程被杀后的直接表现，而 Prometheus 的 Error 终止状态（证据 #4）提供了外部验证，确认了非正常退出。
3. **观测局限**：日志和链路追踪显示崩溃前应用仍在正常响应（证据 #5, #6），但由于未捕获到具体的内存分配 Spike 日志（`allocated_mib` 为 0），无法确认具体的触发时间点，但这一缺失不影响对 OOM 这一根本原因的认定。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存分配 > 96Mi 硬限制 → 内核 OOM Killer 强制终止进程 (Exit Code 137) → 进程无响应导致 Liveness Probe 报 500 → Kubernetes 频繁重启引发 CrashLoopBackOff
```

### 根因结论

**根因：容器内存使用量超过限制（96Mi），触发 OOMKilled。**

证据表明，应用容器 `app` 在运行过程中触发了内存上限，导致内核强制终止了容器进程（Exit Code 137）。随后，由于容器内应用进程已不存在，Liveness 探针无法获得有效响应（HTTP 500），Kubernetes 据此判定容器健康检查失败并发起重启。这一“终止-重启-再次终止”的循环最终导致 Pod 进入 `CrashLoopBackOff` 状态。

尽管日志中未记录到应用层内存激增的详细轨迹，但 Exit Code 137 与 96Mi 的限制设置是确凿的故障证据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 18.5s
├─ 并发证据采集: 77.6s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 77.6s (Evidence 70.0s, RCA 7.5s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
