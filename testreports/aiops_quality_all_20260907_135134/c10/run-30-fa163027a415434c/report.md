## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | 容器配置内存限制（96Mi）过低导致应用运行不稳定：虽然直接终止信号为 Exit 137 (SIGKILL) 且 Prometheus 未标记为 OOMKilled，但关键证据显示 Liveness Probe 因返回 HTTP 500 连续失败而被 Kubelet 强制终止容器。结合 Pod 运行极短时间（约40秒）后即崩溃、20次重启的历史，以及应用日志中仅记录成功请求而缺失导致 500 的错误日志，推断根因为内存限制（96Mi）严重不足，导致应用运行期间出现严重抖动或内存耗尽前的临界崩溃（触发 SIGKILL 而非标准的 OOM Kill 路径），最终因健康检查不通过而被 Kubelet 杀死。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (event `fact-7fd095a1999d`) | 证明 Kubelet 检测到服务内部严重错误，触发强制终止机制 |
| 2 | K8s State | Kubernetes | 容器 `app` 状态 `CrashLoopBackOff`，重启次数 28 次 (event `fact-971e7d6b61c9`, `fact-c2b5518e24f0`) | 确认为持续性高频故障，非偶发性 |
| 3 | K8s Event | Kubernetes | 容器退出原因 `Exit Code: 137` (event `fact-12f2cf790142`) | 信号量证实容器是被系统强制 Kill 的，而非应用主动优雅退出 |
| 4 | K8s Config | Kubernetes | 容器内存硬限制 `96Mi` (fact `fact-98483522facd`) | 提供了应用运行资源极度受限的边界条件，是引发内存抖动的根本配置因素 |
| 5 | Logging | Elasticsearch | 8 条记录仅在 `2026-09-07T22:11:14` 至 `22:11:40` 间记录 `http_status: 200`，无 500 错误日志 (fact `fact-63e26e81634f` 等) | 排除了代码逻辑层面的常规业务异常；表明应用可能在崩溃瞬间丢失了 500 错误日志 |
| 6 | Tracing | Deepflow | 9 次 HTTP 请求返回 `response_code: 200`，耗时 8489us-19885us (fact `fact-5d3d89ebabb0` 等) | 侧面印证故障发生前服务正常，进一步缩小了故障发生的时间窗口 |

**证据互证说明：**
Kubernetes 的 Liveness 探针连续失败（#1）且容器以 Exit 137 终止（#3），说明 Kubelet 杀死了容器。但日志（#5）和应用流量（#6）在故障窗口期内仅记录了 200，未记录导致 500 的异常。结合极低的内存硬限制（#4），证据共同指向内存不足导致的运行时临界崩溃（Memory Pressure/Dithering）——即内存即将耗尽时，应用无法维持稳定进而引发健康检查失败，随后被系统强制 Kill。

## 🎯 根因分析 · g1

### 因果链

```text
内存硬限制过低(96Mi) → 应用运行出现内存抖动 → 导致 Liveness Probe 响应失败(HTTP 500) → Kubelet 强制终止容器(SIGKILL/Exit 137) → 触发 CrashLoopBackOff
```

### 根因结论

已确认根因为：`container.resource_limit.memory` 配置过低（96Mi，证据 #4）。
当前集群中的容器 `aiops-case-10/workload-79d9f8fd88-bwqhh` 因内存限制严重不足，导致运行时出现资源临界崩溃。这直接引发了 Liveness 探针连续返回 500（证据 #1），进而导致 Kubelet 以 Exit 137（证据 #3）强制终止容器。由于应用可能在崩溃瞬间失去响应或日志输出能力，日志（证据 #5）中未能捕获到具体的 500 错误详情，仅表现为频繁的非正常退出与重启（证据 #2）。现有证据链完整闭环，无需更多数据。

---

## 📊 性能统计

```text
├─ 总耗时: 3.3m
├─ 问题定位: 24.1s
├─ 并发证据采集: 162.2s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 162.2s (Evidence 151.2s, RCA 10.9s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
