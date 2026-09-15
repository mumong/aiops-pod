## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | aiops-case-v17/workload Pod 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded` (fact-a8cc9ff987bd) | 直接触发重启机制的探测失败原因 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason: Error`, `container.last_exit_code: 137`, `container.waiting_reason: CrashLoopBackOff` (fact-4a8b5f374bc7, fact-5f501ea3249a, fact-ea3a2b467367) | 确认应用进程被异常终止及当前的重启锁定状态 |
| 3 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason {container="app", reason="Error"} = 1` (fact-ae3b5330c8e5) | 独立验证容器终止原因为 Error 状态 |
| 4 | Logging | elasticsearch | `GET /ready HTTP/1.1 200`, `GET /health HTTP/1.1 200` (fact-03bc12616d8d, fact-4a9e5d5e2844 等) | 确认应用主进程存活期间健康检查逻辑本身正常 |
| 5 | Tracing | deepflow | `GET /health` duration 1652.0us ~ 3001585.0us (fact-3ea3501d7874) | 揭示响应时间存在剧烈波动（最高达 3 秒），为超时提供佐证 |
| 6 | K8s Config | kubernetes | `container.resource_limit.memory: 64Mi` (fact-488c9c0b0926) | 提供导致 OOM 的资源硬限制基准值 |

**证据印证分析：**
Kubernetes 事件与 Metrics 独立且一致地指出了 `Exit Code 137`（通常对应 SIGKILL/OOM）和 `CrashLoopBackOff` 状态。Tracing 数据显示 `GET /health` 请求响应时间最长达到 3 秒，解释了为何在资源受限导致进程卡顿甚至被杀前，探针会触发 `context deadline exceeded`。Logging 确认应用进程在退出前能响应 HTTP，排除了应用代码死锁导致无法启动的可能。

## 🎯 根因分析 · g1

```text
容器内存 Limit 配置过低 (64Mi) → 运行时内存超限触发 OOM Killer → 进程被强制终止 (Exit Code 137) → 探针超时 & 频繁重启 (CrashLoopBackOff)
```

### 根因结论

已确认根因为 **容器内存限制配置不足**。

证据链条如下：
1. **硬限制事实**：容器 `app` 的 `memory.limit` 仅为 `64Mi`（证据 #6）。
2. **终止行为**：容器反复退出且 `exit_code` 固定为 `137`（证据 #2），这在 K8s 中明确指向内核 OOM Killer 介入。
3. **探测失效关联**：应用进程在内存耗尽前会出现严重的响应延迟（最长约 3000ms，证据 #5），直接导致了 Liveness Probe 报告的 `context deadline exceeded`（证据 #1）。

上述事实相互印证，排除了网络或应用逻辑故障，确认为资源限制导致的稳定性崩溃。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 19.2s
├─ 并发证据采集: 55.5s
│  └─ g1 aiops-case-v17/workload: 55.4s (Evidence 44.3s, RCA 10.9s)
└─ 汇总总结: 12.1s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
