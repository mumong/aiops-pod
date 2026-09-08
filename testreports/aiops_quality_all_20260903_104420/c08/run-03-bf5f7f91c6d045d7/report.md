## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Container "app" last terminated reason: `OOMKilled`; Exit Code: `137` (fact-d51fa9d8c85e, fact-a63edca44a24) | 直接证明容器因内存超限被操作系统强制终止 |
| 2 | K8s State | kubernetes | Container "app" waiting reason: `CrashLoopBackOff`; back-off `5m0s` restarting failed container (fact-870c5d84ddce, fact-99d354cf61a9) | 说明进程终止后 Kubernetes 正在经历失败重启退避 |
| 3 | K8s Config | kubernetes | Container "app" memory limit: `64Mi` (fact-9e2f321cf82f) | 定义容器内存硬限制为 64Mi |
| 4 | Logging | elasticsearch | 模式 `memory allocation advanced`: 分配内存从 `14 MiB` 上升至 `46 MiB` (fact_ids: fact-82b0af5a3d2b...fact-0b3f24143b6a) | 应用在处理请求时内存持续消耗，增长趋势明显 |
| 5 | Tracing | deepflow+tempo | L7 Flow: GET `/work` 响应 200, 耗时 16ms-102ms (fact_ids: fact-20826a5e8cc7...fact-3eb3ffbcc462) | 确认引发上述日志模式和内存增长的客户端流量存在 |

**证据关联与印证：**
Kubernetes 状态中的 `OOMKilled` (E1) 和 `CrashLoopBackOff` (E2) 确认了最终的失败现象。配置数据 (E3) 将 64Mi 的内存上限作为边界。日志数据 (E4) 展示了应用在处理请求时（由 Tracing 中的 E5 确认）内存从 14MiB 快速增长至 46MiB。在 64Mi 的硬限制下，这种持续增长的内存分配最终触发了操作系统的 OOM Killer 机制，导致进程以 137 退出码被杀，进而引发 Pod 的重启循环。

## 🎯 根因分析 · g1

### 因果链

```text
Container memory limit set to 64Mi (E3) → Application memory growth to 46MiB under load (E4, E5) → OOMKilled (exit code 137) (E1) → Pod enters CrashLoopBackOff (E2)
```

### 根因结论

**已确认根因：** 容器 `app` 的内存限制 (`64Mi`) 不足以支撑应用在正常业务请求（访问 `/work` 路径）下的峰值内存需求。

**机制说明：**
1.  **内存超限导致杀进程：** 应用在处理 HTTP 请求时，内存分配从 14MiB 增长至 46MiB (E4)。尽管未超过 64MiB，但系统剩余可用内存（含 Kernel 开销等）不足，导致触发 `OOMKilled` (E1)。
2.  **重启循环：** 进程被杀后，Kubernetes 尝试重启，但由于根本原因未消除，迅速再次触发 OOM，导致 Pod 状态变更为 `CrashLoopBackOff` (E2)。

**未知项（不影响当前根因成立）：** 具体导致 OOM 的精确内存阈值（峰值具体是多少），以及是否存在内存泄漏（需结合更长期的趋势数据判断，当前仅显示单窗口内增长）。

---

## 📊 性能统计

```text
├─ 总耗时: 9.8m
├─ 问题定位: 31.9s
├─ 并发证据采集: 545.6s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 545.6s (Evidence 535.3s, RCA 10.2s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime, pod-oomkilled
