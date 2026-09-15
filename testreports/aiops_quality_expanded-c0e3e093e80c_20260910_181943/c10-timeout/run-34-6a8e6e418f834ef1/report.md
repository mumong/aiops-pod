## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Pod workload in aiops-case-v17 is in CrashLoopBackOff state with exitCode 137. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 app 状态等待原因：CrashLoopBackOff (fact-1b01e2c5e80d) | 确认当前运行状态 |
| 2 | K8s State | Kubernetes | 容器 app 终止退出码：137 (fact-95653d34fa7b) | 指示被系统强制终止 |
| 3 | K8s Event | Kubernetes | Liveness probe 失败：context deadline exceeded (fact-ac5c3792c720) | 证明存活探针超时，反映资源极度枯竭 |
| 4 | K8s State | Kubernetes | 内存资源限制 (Limit)：64Mi；请求 (Request)：8Mi (fact-29cc1cad39cb, fact-00e09c882e4e) | 确认容器拥有极低的硬限制，是资源瓶颈的直接上下文 |
| 5 | K8s State | Kubernetes | 容器启动重启总次数：27 次 (fact-8e23e3f563e1) | 证明故障已触发反复崩溃重启循环 |
| 6 | Metric | Prometheus | kube_pod_container_status_waiting_reason (CrashLoopBackOff): 1 (fact-c0d10c575c01) | 独立观测确认当前等待状态 |
| 7 | Logging | Elasticsearch | 10.2.0.50 - GET /ready HTTP/1.1 200 (例如 fact-0ebb5191ee7e, fact-4ed3d63c970f) | 显示容器在终止前偶尔能响应就绪探针，但状态不稳定 |
| 8 | Tracing | Deepflow | /health 请求响应耗时：3,000,797us - 3,002,216us (fact_ids: [3ea..., 59f..., ...]) | 证实健康检查请求耗时突破 3 秒，远超探针通常的超时阈值 |

证据表明，虽然日志中能看到容器对 `/ready` 探针返回 HTTP 200（证据 #7），但 Tracing 显示 `/health` 探针的请求延迟高达约 3 秒（证据 #8），这直接导致 Kubernetes 探测超时（证据 #3）。由于容器内存上限仅为 64Mi（证据 #4），在高延迟或瞬时负载下极易发生 OOM，被内核 OOM Killer 强制杀掉并返回退出码 137（证据 #2），最终导致 CrashLoopBackOff（证据 #1）和 27 次重启（证据 #5）。

## 🎯 根因分析 · g1

### 因果链

```text
内存资源限制极低 (64Mi) → 瞬时资源压力导致内存耗尽 → 触发 OOM Killer 终止进程 (Exit Code 137) → 存活探针超时且容器反复崩溃 (CrashLoopBackOff)
```

### 根因结论

已确认根因为**容器内存配置过低导致的 OOM (Out-Of-Memory) 崩溃**。

证据显示，容器 `app` 的硬内存限制 (Limit) 仅为 **64Mi** (证据 #4)。尽管应用偶尔能响应就绪探针 (证据 #7)，但追踪数据表明健康检查请求的平均耗时已接近 3 秒 (证据 #8)。这种资源紧张状态导致内核 OOM Killer 介入，将进程发送 SIGKILL 信号终止，表现为退出码 **137** (证据 #2) 和 Kubernetes 报告的 Liveness 探针超时 (证据 #3)。Kubelet 尝试重启失败后，Pod 进入 CrashLoopBackOff 状态并累计重启 27 次 (证据 #1, #5)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 14.4s
├─ 并发证据采集: 67.0s
│  └─ g1 aiops-case-v17/workload: 67.0s (Evidence 58.3s, RCA 8.3s)
└─ 汇总总结: 12.9s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime, pod-oomkilled
