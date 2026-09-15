## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | pod 状态: Running; 容器 app 状态: CrashLoopBackOff | 确认 Pod 存活但应用持续失败 |
| 2 | K8s Event | Kubernetes | Warning BackOff 4m25s (x580 over 129m) kubelet Back-off restarting failed container app | 确认容器经历了高频重启 |
| 3 | K8s Config | Kubernetes | container app memory limit: 64Mi; cpu limit: 100m | 提供容器资源硬限制上限 |
| 4 | K8s State | Kubernetes | container app last terminated reason: OOMKilled; exit code: 137 | 直接证明因内存溢出被系统强制终止 |
| 5 | K8s State | Kubernetes | container app resource request memory: 8Mi; cpu request: 5m | 确认初始调度的资源请求极低 |
| 6 | Metric | Prometheus | kube_pod_container_status_restarts_total: 30 (container: app) | 量化证实了容器的高频重启现象 |
| 7 | Metric | Prometheus | kube_pod_container_status_last_terminated_reason: 1 (reason: OOMKilled, container: app) | 确认最后一次终止原因为内存溢出 |
| 8 | Logging | Elasticsearch | startup allocation 256Mi | 揭示应用启动阶段的具体资源需求 |

**证据关联说明：**
Kubernetes 的 OOMKilled 终止记录与退出码 137 (fact 4) 与 Prometheus 指标中的 OOMKilled 状态 (fact 7) 相互印证，确证了容器是被系统级内存限制杀死的。日志中的启动分配 256Mi (fact 8) 与 Kubernetes 配置的 64Mi 内存上限 (fact 3) 形成了直接的因果关系解释，说明应用请求的资源远超集群允许的范围。高频的 BackOff 警告 (fact 2) 与 Metrics 中的 30 次重启计数 (fact 6) 共同描述了这一现象造成的用户可见后果。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动请求 256Mi 内存 (事实 8) > Pod 配置的 64Mi 硬限制 (事实 3) → 触发 Linux OOM Killer 终止进程 (事实 4) → 触发 kubelet 重启机制 (事实 2) → 陷入 CrashLoopBackOff (事实 1)
```

### 根因结论

**已确认的根因：**
容器 `app` 的启动行为试图分配 256Mi 内存，该值超出了 Kubernetes 为该容器设定的 `memory` 硬限制（64Mi）。这导致 Linux 内核 OOM Killer 介入并杀死了该进程（退出码 137），进而引发 Kubernetes 重启策略的反复尝试，最终使 Pod 进入 CrashLoopBackOff 状态。

该结论由以下事实链共同支撑：
1.  **资源限制事实**：容器配置了 64Mi 的内存上限 (fact-3fee036fb6dd)。
2.  **需求冲突事实**：日志明确记录了应用启动时分配了 256Mi 内存 (fact-07987e0ef46e)。
3.  **失败机制事实**：容器以 OOMKilled 原因被终止且退出码为 137 (fact-86d53c6b8cde, fact-0b72f55fc165)。
4.  **状态一致性**：Prometheus 指标独立证实了该容器以 OOMKilled 原因被终止 (fact-b246f03e60df) 且发生 30 次重启 (fact-11848d1eb075)。

---

## 📊 性能统计

```text
├─ 总耗时: 9.7m
├─ 问题定位: 20.4s
├─ 并发证据采集: 550.9s
│  └─ g1 aiops-case-v15/workload: 550.9s (Evidence 542.2s, RCA 8.5s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
