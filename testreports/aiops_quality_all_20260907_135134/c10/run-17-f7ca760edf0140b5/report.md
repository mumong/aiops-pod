## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | {'message': 'Exit Code:    137'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Exit Code: 137, Container Restart Count: 18 | 确认容器频繁异常退出且进程被终止 |
| 2 | K8s Event | Kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 | 证实 Liveness Probe 返回 500 错误 |
| 3 | K8s Config | Kubernetes | resource_limit.memory: 96Mi, resource_limit.cpu: 200m | 确认容器存在硬资源限制，为 OOM 排查提供背景 |
| 4 | K8s Event | Kubernetes | Killing [app]: Container app failed liveness probe, will be restarted | 证明 Pod 当前处于由 Liveness 探针失败触发的终止流程中 |
| 5 | Metric | Prometheus | kube_pod_container_status_restarts_total: 18 | 与 K8s State 数据互相印证，确认异常频繁发生 |
| 6 | Logging | Elasticsearch | Pattern: `http_request` completed, `http_status`: 200, `path`: `/work` | 确认应用在崩溃前能正常处理请求，未报应用层错误 |

1. 证据 1 指出进程以 Exit Code 137 被杀，这通常意味着被 OOM Killer 或 Liveness Probe Killer 终止，仅凭此无法区分具体原因。
2. 证据 2、4 证实了 Liveness Probe 失败确实是触发容器重启的直接事件机制。
3. 证据 6 表明应用本身并未报错，结合证据 1 的 137 退出码，存在应用因无响应（导致 Probe 500）或内存超限（导致 OOM 进而导致无响应）两种可能。
4. 由于缺失 crash 前的详细内存指标（Metric 中未覆盖）和崩溃瞬间的最后日志，无法证实是 OOM 还是单纯的超时。

## 🎯 根因分析 · g1

### 因果链

```text
应用响应缓慢或资源受限 → Liveness Probe HTTP 500 失败 → Kubelet 触发 Container Kill (Exit Code 137) → Pod 进入 CrashLoopBackOff
```

### 根因结论

证据显示 Pod 频繁退出（Exit Code 137）且伴随 Liveness Probe 失败（500），确认了当前的触发机制是 **Liveness 探针超时导致的容器终止**。

但是，**根本原因（Root Cause）证据不足**。Exit Code 137 既可能是 Liveness Probe 机制触发的 Kill，也可能是 OOM Killer 触发的 Kill。由于：
1. 缺失 Pod 在崩溃前的内存使用指标（Metric 数据不支持趋势判断或仅确认了重启数）；
2. 缺失容器崩溃前最后时刻的日志以排除应用层 OOM 报错；
3. 缺乏能够证明资源耗尽的定量事实。

因此，当前诊断无法在“OOM Killed”与“Liveness Probe Kill”之间做出唯一判定，诊断状态为 inconclusive。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.6s
├─ 并发证据采集: 49.2s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 49.2s (Evidence 40.8s, RCA 8.2s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
