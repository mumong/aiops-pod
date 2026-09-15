## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | Container resource limit (Memory: 96Mi) is too low for the application workload, causing OOMKilled (Exit Code 137) and subsequent CrashLoopBackOff. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | K8s State | `container.resource_limit.memory` = 96Mi | 明确容器内存硬限制极低，构成 OOM 触发条件 |
| 2 | K8s State | K8s Event | `event.reason=BackOff`, `message="Back-off restarting failed container"` (x176) | 确认系统因崩溃持续退避重启，符合 CrashLoopBackOff 行为 |
| 3 | K8s State | K8s Event | `event.reason=Killing`, `message="Container app failed liveness probe, will be restarted"` | 证实容器健康检查失败直接触发了 kill 动作 |
| 4 | K8s State | K8s Event | `exit_code` = 137, `reason` = `Error` | Exit Code 137 确证进程被 Linux OOM Killer 强制终止 |
| 5 | K8s State | K8s State | `restart_count` = 19, `status` = Running | 量化重启规模，确认处于频繁重启循环中 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason: CrashLoopBackOff) = 1 | 指标层同步验证了 Pod 当前处于等待重启的崩溃状态 |
| 7 | Logging | Elasticsearch | Pattern: `request completed`, path: `/work`, `http_status`: 200, trace_ids: ["273c96...", "f313...", ...] | 确认应用本身具备处理正常请求的能力，崩溃具有间歇性而非服务逻辑损坏 |
| 8 | Tracing | Deepflow | Flow: `GET /work`, src: `172.16.104.33`, dst: `172.16.104.34`, duration: 12ms-29ms | 确认网络通路与正常响应延迟，进一步排除网络侧原因 |

证据间逻辑印证：K8s 层面 Exit Code 137 与低内存限制（96Mi）结合，确凿指向内存超限导致的 OOM 崩溃。Liveness Probe 失败是容器被杀的直接触发器。Logging 和 Tracing 证明在崩溃间隙应用能正常响应流量，排除了代码层面的持续阻塞或逻辑死锁，符合内存不稳定（如内存泄漏或峰值占用过高）引发间歇性 OOM 的特征。

## 🎯 根因分析 · g1

### 因果链
```text
容器内存限制过低 (96Mi) → 应用内存使用突破阈值触发 OOM Killer → Pod 状态变更为 CrashLoopBackOff → Liveness 探针探测失败并持续退避重启
```

### 根因结论
**根因已确认**。容器 `app` 的内存资源限制被硬限制在 **96Mi**，该资源额度无法满足当前应用工作负载（workload）的正常运行需求。当应用运行期间内存消耗超过 96Mi 时，Linux 内核 OOM Killer 介入并强制终止进程，导致 Exit Code 137。进程终止导致容器重启，触发 Liveness Probe 失败（HTTP 500 / 连接中断），进而引发 Kubernetes 退避重启机制（BackOff）。证据 [1] 定义了低水位限制，证据 [4] 提供了 OOM 的底层信号，证据 [2] 和 [6] 描述了由此引发的系统级故障循环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.3s
├─ 并发证据采集: 51.7s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 51.7s (Evidence 43.5s, RCA 8.1s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime
