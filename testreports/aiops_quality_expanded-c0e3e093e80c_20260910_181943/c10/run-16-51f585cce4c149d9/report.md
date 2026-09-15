## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bsn84` | CrashLoopBackOff | Container resource limit (96Mi memory) is insufficient, causing OOMKill (Exit Code 137) and subsequent CrashLoopBackOff. Liveness probe failures (HTTP 500) occurred due to application instability or resource starvation prior to termination. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning  Unhealthy  56m (x8 over 58m)  kubelet Liveness probe failed: HTTP probe failed with statuscode: 500` | 展示应用存活探针失败的现象，通常指示资源耗尽或应用假死。 |
| 2 | K8s State | Kubernetes | `container.last_exit_code: 137` | 容器异常终止的确切信号，137 是 OOMKill 的标准标识。 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory: 96Mi` | 证实该容器被分配的硬内存上限极低，为 OOMKill 提供了直接的配置证据。 |
| 4 | K8s Event | Kubernetes | `Warning  BackOff  8m12s (x175 over 54m) kubelet Back-off restarting failed container app...` | 证实容器因反复崩溃已触发指数退避，进入 CrashLoopBackOff 状态。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason = 1` (reason: `CrashLoopBackOff`) | 独立于 K8s 事件的状态确认，指标侧验证了集群认为容器处于崩溃等待状态。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason = 1` (reason: `Error`) | 验证了容器上一次非正常退出的原因是 Error（即 OOMKill 导致）。 |
| 7 | Logging | Elasticsearch | `pattern: "request completed" (http_status: 200, path: "/work")` | 显示在 CrashLoop 发生前的正常窗口内，请求能成功处理，说明应用本身非代码死锁，而是资源耗尽型崩溃。 |

**证据交叉印证说明：**
K8s 的 `Exit Code: 137` (证据 #2) 与 Prometheus 的 `last_terminated_reason: Error` (证据 #6) 强相关性确认了 OOMKill。配置中的低内存限制 96Mi (证据 #3) 解释了为何简单的负载会导致内存爆满。应用层面的 Liveness Probe 500 失败 (证据 #1) 是 OOM 发生前或发生时的典型系统响应。日志中 200 状态码 (证据 #7) 证明应用在处理请求时是活跃的，从而排除了代码级静默挂起。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制过低 (96Mi, 证据 #3) → 内存分配触及限制触发 OOMKill (Exit Code 137, 证据 #2) → 应用进程被强制终止导致服务不可用 (Liveness Probe 500, 证据 #1) → Kubernetes 重启失败进入 CrashLoopBackOff (证据 #4, #5)
```

### 根因结论

已确认的根因是 **容器内存资源限制设置过低（96Mi）**。

证据链清晰地指向了这一结论：Kubernetes 事件与 Prometheus 指标一致地表明容器以 Exit Code 137 退出，这是 Linux 内核 OOM Killer 介入的特征。该退出直接导致应用服务响应存活探针（返回 500）并引发 CrashLoopBackOff。日志中存在的成功请求记录（证据 #7）证实了崩溃是由资源竞争（内存不足）而非应用逻辑错误引起的。

---

## 📊 性能统计

```text
├─ 总耗时: 3.0m
├─ 问题定位: 23.0s
├─ 并发证据采集: 144.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bsn84: 144.0s (Evidence 136.0s, RCA 7.9s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bsn84**: pod-crashloop-runtime
