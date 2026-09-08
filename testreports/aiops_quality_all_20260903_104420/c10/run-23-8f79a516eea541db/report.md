## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Pod app容器配置的内存Limit（96Mi）过低，导致应用在处理请求时触发OOM Killer被系统强制终止（Exit Code 137）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Exit Code: 137 (fact-09cb4ee6fc85, fact-853d0d0d3d7d) | 直接证据，OOM Killer 终止进程的标准信号 |
| 2 | K8s State | Kubernetes | Memory Limit: 96Mi (fact-012f81acce81) | 根因，极低的硬限制约束了容器可用内存 |
| 3 | K8s Event | Kubernetes | BackOff / Liveness probe failed: statuscode: 500 (fact-3b6aac150905, fact-e22c21f7235b) | 现象验证，探针失败确认进程处于不可用状态 |
| 4 | K8s State | Kubernetes | Restart count: 23 (fact-6762180f9c4f) | 状态验证，高频重启对应 CrashLoopBackOff |
| 5 | Metric | Prometheus | kube_pod_container_status_waiting_reason: 1 (CrashLoopBackOff) (fact-642e6a15e584) | 聚合状态印证，当前处于等待重启状态 |
| 6 | Metric | Prometheus | kube_pod_container_status_last_terminated_reason: 1 (Error) (fact-e908d3984355) | 聚合状态印证，上一次终止原因为非零退出 |
| 7 | Logging | Elasticsearch | request completed /work (HTTP 200) (fact-1c4e78a3af26, etc.) | 上下文：进程在崩溃前曾成功处理过请求 |

**证据小结**：Kubernetes State 记录到 Exit Code 137 配合 Memory Limit 96Mi 构成了 OOM 的完整证据链；Metrics 确认了 CrashLoopBackOff 和 Error 状态；K8s Events 记录了由此引发的 Liveness Probe 失败；Logs 证明了应用并非初始启动即失败，而是具备处理能力但受限于资源被杀。

## 🎯 根因分析 · g1

### 因果链

```text
内存 Limit (96Mi) 设置过低 → 处理请求时内存耗尽触发 OOM Killer → 进程强制终止 (Exit Code 137) → 容器重启循环 (CrashLoopBackOff)
```

### 根因结论

已确认根因为 **容器资源限制配置不当**。
应用 Pod (`workload-79d9f8fd88-sbqvc`) 的 `app` 容器配置的内存硬限制（Memory Limit）仅为 `96Mi`。当应用处理请求时内存需求突破此限制，操作系统 OOM Killer 介入终止进程（证据 #1, #2）。这直接导致容器状态变更为 CrashLoopBackOff（证据 #4, #5, #6）及健康检查失败（证据 #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 3.2m
├─ 问题定位: 36.0s
├─ 并发证据采集: 148.1s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 148.1s (Evidence 142.0s, RCA 5.9s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
