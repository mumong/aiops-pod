## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | {'message': 'cni.projectcalico.org/podIPs: 172.16.104.31/32'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: CrashLoopBackOff (fact-a64b83d3092e) | 确认应用容器进入循环重启状态。 |
| 2 | K8s Event | Kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 (fact-884d68f6db64) | 暴露 Liveness Probe 端点当前直接返回 500 错误，导致 kubelet 判定不健康。 |
| 3 | K8s Event | Kubernetes | Exit Code: 137 (fact-69b39cf6e2a8) | 证明容器进程曾因 SIGKILL 被内核终止，存在严重内存压力。 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory`: 96Mi (fact-30fc12d49462) | 提供判断 OOM 的关键阈值依据。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` (reason=Error) 持续为 1 (fact-1afe102a9f06) | 侧面印证上一次异常终止并非普通 OOMKilled，或者 OOMKilled 被归类为 Error，需结合 Exit 137 确认。 |
| 6 | Logging | Elasticsearch | HTTP request completed /work (status: 200, count: 8) (fact-0cb579bdca80) | 提供反面证据，显示业务核心路径在近期运行正常，阻断并非发生在业务逻辑本身。 |

**证据互证分析：**
Kubernetes 事件（#2）显示 Liveness Probe 失败是因为端点直接返回 500，而非无响应（这通常意味着进程存活但业务崩溃），同时（#3）又留下了 Exit Code 137 的记录。日志数据（#6）证实应用在处理业务流量 `/work` 时是健康的。这两者的矛盾表明，**故障是间歇性的**：容器可能因为瞬时 OOM 被 SIGKILL（#3）后重启，但在重启后不久应用再次崩溃返回 500（#2）导致被杀死。由于缺乏内存监控指标（#4 仅提供了阈值），无法直接断定是内存不足导致了这种反复崩溃。

## 🎯 根因分析 · g1

```text
未知 (可能是间歇性 OOM 或 500 业务 Bug) → 容器进程被杀死 (137) 或 应用崩溃 (500) → 容器持续重启 (CrashLoopBackOff) → Pod 状态 CrashLoopBackOff
```

### 根因结论
**证据不足**。
当前现象确认为容器因异常退出（Exit 137 / SIGKILL）及探针失败（500）导致的 CrashLoopBackOff。然而，现有证据中存在逻辑冲突：日志显示业务核心路径 `/work` 正常（#6），这通常意味着容器进程并未长期处于“假死”状态；但 Exit Code 137 又强指向 OOMKilled。

由于缺乏以下决定性事实，无法区分根因是“内存限制过紧（96Mi）引发瞬时 OOM 导致容器被杀”还是“应用存在间歇性 Bug 导致 /health 端点返回 500，进而引发重启”：
1. **缺失内存监控数据**：无法确认容器在崩溃前是否达到了 96Mi 的内存限制。
2. **缺失 Liveness Probe 日志**：当前的 500 错误可能由崩溃的副产物导致，也可能是导致崩溃的原因（如果是 Bug，为什么 Exit Code 是 137？如果是 OOM，为什么探针有返回 500 的机会而不是无响应？）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 21.3s
├─ 并发证据采集: 82.3s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 82.3s (Evidence 72.0s, RCA 10.0s)
└─ 汇总总结: 12.7s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
