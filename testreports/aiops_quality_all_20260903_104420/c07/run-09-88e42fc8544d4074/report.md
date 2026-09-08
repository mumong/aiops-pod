## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-kmfxx 处于 CrashLoopBackOff，容器 app 反复重启且 Readines 为 False。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase: Running`, `container.waiting_reason: CrashLoopBackOff` (fact-187781168b31, fact-0e9c0bc9ba4a) | 确认 Pod 存活但容器反复进入崩溃重启循环。 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason: Error`, `container.last_exit_code: 78` (fact-107a6aa4ccf6, fact-0aee1edb0009) | 确定崩溃机制为进程退出码 78（应用层错误退出，非资源超限）。 |
| 3 | K8s Event | Kubernetes | `BackOff restarting failed container app` 66次 (fact-47db3faa98ba) | 证实崩溃重启频率极高，触发指数退避策略。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"} = 1` (fact-5ce1011b07aa) | 外部监控确认集群处于崩溃等待态。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 7` (fact-e14a601b81b4) | 量化重启次数，确认状态持续恶化。 |
| 6 | Logging | Elasticsearch | `http_request` 模式 8 次：`level=error`, `message="CONFIG_MISSING"`, `http_status=500`, `path="/work"` (fact-1dfce90a25bc et al.) | 直接暴露崩溃前的具体异常原因为“缺少配置”。 |
| 7 | Tracing | Deepflow | HTTP Flow: `GET /work` → `status=500`, `dst_ip=172.16.104.15` (fact-522bcae1d3d8) | 从流量层证实 Pod IP 在 `/work` 接口持续返回应用层错误，无超时或网络中断。 |
| 8 | Tracing | Tempo | Span `GET /work`: `attributes.aiops.observed_mode=config_missing_exit` (fact-9621698453cf) | 从 Trace 维度进一步锁定崩溃原因为配置缺失导致的退出模式。 |

**证据关联说明：**
K8s 层面（#1, #2）记录了崩溃的结果（Exit 78），而应用层面日志（#6）和链路追踪（#7, #8）解释了具体的崩溃诱因（HTTP 500 + CONFIG_MISSING）。Trace 中记录的 `aiops.observed_mode`（#8）直接关联了退出码 78 与配置缺失的逻辑，排除了资源（#5）或网络故障的可能。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码访问不存在的配置键(unknown) → 处理请求时触发 CONFIG_MISSING 异常并返回 HTTP 500 → 容器进程因未处理异常崩溃退出 (exitCode=78) → Pod 进入 CrashLoopBackOff (restarts=7)
```

### 根因结论

**已确认根因：**
Pod `aiops-case-07/workload-dff5cbc6b-kmfxx` 处于 `CrashLoopBackOff` 状态的根本原因是**应用程序在处理请求时发生配置缺失异常**。

具体证据支持如下：
1.  **异常触发**：Elasticsearch 日志显示在崩溃前多次发生 `level=error` 的日志记录，明确指出 `message="CONFIG_MISSING"`，且 `path="/work"` 接口返回 `http_status=500`（见证据 #6）。
2.  **机制确认**：Deepflow 流量记录证实了该 Pod 的 `/work` 接口确实持续返回 `status=500`，排除了网络或基础设施层面的连接问题（见证据 #7）。
3.  **模式匹配**：Tempo 链路数据中的 `aiops.observed_mode=config_missing_exit` 将这种退出行为与配置缺失直接关联，确认进程因应用逻辑缺陷而非资源限制（OOM）或外部探针失败而退出（见证据 #8）。
4.  **结果印证**：容器退出码为 `78`（见证据 #2），结合上述日志，证实了应用层崩溃导致了 Kubernetes 的重启循环。

**未知/待确认事项：**
*   导致 `CONFIG_MISSING` 的具体缺失 Key 名称：现有证据仅能证明配置项缺失，但无法指出具体是哪一个 Key 缺失（如 "fact-1dfce90a25bc" 中的具体上下文未展示）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 21.2s
├─ 并发证据采集: 70.1s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 70.1s (Evidence 59.1s, RCA 10.8s)
└─ 汇总总结: 15.6s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
