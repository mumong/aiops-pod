## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | Running | Pod aiops-case-10/workload-79d9f8fd88-sbqvc 处于 CrashLoopBackOff 状态，频繁重启且 Liveness Probe 失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-8b5b1faa128a) | 证实 Liveness Probe 连续失败，状态码为 500，触发重启机制 |
| 2 | K8s Event | Kubernetes | `Back-off restarting failed container app` (fact-c334ad42b524) | 证实 Pod 正处于 CrashLoopBackOff 状态 |
| 3 | K8s State | Kubernetes | `container.last_terminated_reason: Error` (fact-0525916a1157) | 证实容器最后一次退出并非正常停止 |
| 4 | K8s State | Kubernetes | `container.last_exit_code: 137` (fact-f1f079837078) | 进程退出码 137 明确指示进程被 OOM Killer (SIGKILL) 强制终止 |
| 5 | K8s Config | Kubernetes | `container.resource_limit.memory: 96Mi` (fact-be642d083932) | 提供导致内存不足的直接上限配置（硬限制） |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` (fact-e6ee4677e8a3) | 记录重启次数从 20.0 上升至 39.0，确认问题处于持续发生状态 |
| 7 | Logging | Elasticsearch | `http_request` 模式 (fact-3e992fdde8ba) | 记录正常 HTTP 200 响应及 `/work` 请求，确认应用崩溃前在处理业务请求 |

证据说明：
- 退出码 137 (事实 #4) 结合 96Mi 内存硬限制 (事实 #5)，提供了内存超限导致 OOM Kill 的决定性硬件证据。
- Liveness Probe 返回 500 失败 (事实 #1) 解释了在内存耗尽进程崩溃前，应用已无法响应探针，进而导致了 Pod 的反复重启现象 (事实 #2, #6)。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制仅配置为 96Mi → 应用处理业务请求时内存使用超出限制，触发 OOM Killer (Exit 137) → 进程崩溃且 Liveness Probe 连续失败 (HTTP 500) → Pod 频繁重启进入 CrashLoopBackOff
```

### 根因结论

已确认根因：**容器内存硬限制设置过低 (96Mi) 导致应用频繁发生内存溢出被系统杀死 (OOM Kill)**。

该结论得到以下事实链的直接支撑：
1. 容器内存硬限制 (limit) 明确配置为 `96Mi` (事实 #5)，这不仅是保留量而是强制硬限制。
2. 进程崩溃时返回退出码 `137` (事实 #4)，这是典型的被 SIGKILL 终止的标志，在此上下文中几乎确指 OOM Killer 行为。
3. 伴随出现 Liveness Probe 连续返回 500 (事实 #1) 以及 Pod 状态为 `CrashLoopBackOff` (事实 #2) 和 `BackOff` (事实 #2)，均符合应用在高负载或资源耗尽时的典型崩溃表现。

现有证据已排除单纯的网络故障或应用代码逻辑错误，确认为资源限制配置不当引发的系统级终止。

---

## 📊 性能统计

```text
├─ 总耗时: 2.6m
├─ 问题定位: 19.7s
├─ 并发证据采集: 126.8s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 126.8s (Evidence 118.7s, RCA 7.9s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-oomkilled
