## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Liveness Probe超时配置错误导致容器被强制终止 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded (Client.Timeout exceeded while awaiting headers)` (fact-360a55686867) | 确认 kubelet 检测 Liveness Probe 超时的直接事实 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff (fact-b561d54a2510); `container.last_terminated_reason`: Error (fact-cc2d8192e3d3) | 确认为容器因错误终止导致的重启循环状态 |
| 3 | K8s Event | kubernetes | `Back-off restarting failed container app in pod workload_aiops-case-v17(85aece07-6ffa-41db-9e5a-f351771a8864)` (fact-642ee582a4a3) | 证实容器被反复终止且正在指数级退避重启 |
| 4 | K8s State | kubernetes | `container.last_exit_code`: 137 (fact-67329ac55a2f) | 提供终止原因的关键数值，暗示 OOMKilled 或其他强制终止机制 |
| 5 | K8s Config | kubernetes | `container.resource_limit.memory`: 64Mi (fact-3b645e3ad510) | 确认应用容器存在严格的内存硬限制 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 15 (fact-0fa31ee3678d); `kube_pod_container_status_waiting_reason`: CrashLoopBackOff (fact-89d4bf6c56b4) | 量化确认当前重启次数及等待状态，与 K8s 状态一致 |
| 7 | Logging | elasticsearch | 连续记录中 `/health` 返回 `200` (fact-6ac270ba6283, fact-8ae49aeb1c13) | 证实应用服务进程在容器内确实在监听并处理 `/health` 请求，排除应用进程完全挂死 |
| 8 | Tracing | deepflow | Flow: `GET /health`, `response_code: 200`, duration_us `min: 3001057.0 (approx 3s)` (fact-65edea5f8370等) | 从流量侧确认请求虽然返回成功，但耗时极长（约 3 秒） |

**证据间印证关系说明：**
*   K8s 的 Liveness Probe 超时报错 (Evid 1) 与 DeepFlow 追踪中 `/health` 请求长达 3 秒的响应时间 (Evid 8) 存在直接因果关系：如果探针配置的超时时间小于 3 秒，必然导致探针判定失败。
*   应用日志显示服务正常运行 (Evid 7)，而 Pod 状态为 CrashLoopBackOff (Evid 2)，且终止码为 137 (Evid 4)，说明容器是被外部强制杀死的，而非应用内部逻辑崩溃退出。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制极严(64Mi)或负载过高 → 应用响应延迟飙升至约3秒 → kubelet Liveness Probe 设置超时时间过短(预期<3s) → 探针判定超时并强制终止容器(Pid 137) → 容器进入 CrashLoopBackOff 循环
```

### 根因结论

已确认的根因是 **Liveness Probe 的超时配置（TimeoutSeconds）与应用的实际响应延迟不匹配**。

依据如下证据：
1.  **探针配置不足**：`kubectl` 事件报告 `context deadline exceeded` (Evid 1)，说明超时时间短于请求实际耗时。
2.  **应用仍在运行但缓慢**：DeepFlow 追踪确认 `/health` 返回 200，但耗时长达约 3 秒 (Evid 8)；应用日志也记录成功处理请求 (Evid 7)。这证明应用进程存活，并非完全无响应。
3.  **强制终止与重启**：容器因超时被杀死（Exit Code 137）(Evid 4)，进入 CrashLoopBackOff (Evid 2, Evid 6)。

现有的证据不足以完全断定导致响应变慢的**根本系统原因**（如是否确因 64Mi 内存限制导致 Swap 或 GC 停顿，Evid 5），但导致当前“异常组”中 CrashLoopBackOff 现象的**决定性故障**是探针超时配置不当。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 30.0s
├─ 并发证据采集: 79.5s
│  └─ g1 aiops-case-v17/workload: 79.5s (Evidence 73.6s, RCA 5.7s)
└─ 汇总总结: 16.1s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
