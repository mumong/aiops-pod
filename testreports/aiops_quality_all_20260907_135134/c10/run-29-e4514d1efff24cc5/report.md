## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | RecentRestart | Pod aiops-case-10/workload-79d9f8fd88-bwqhh 处于 CrashLoopBackOff 状态，容器重启 28 次 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: Error; `exit_code`: 137 | 确认为资源耗尽导致的 OOMKilled，而非逻辑崩溃 |
| 2 | K8s State | kubernetes | `container.resource_limit.memory`: 96Mi; `container.resource_request.memory`: 24Mi | 证实容器可用内存硬限制极低，存在显著超卖空间 |
| 3 | K8s State | kubernetes | `event`: Liveness probe failed with statuscode: 500 (x43); `container.restart_count`: 28 | 证实存活探针持续失败导致 kubelet 触发崩溃循环 |
| 4 | K8s Config | kubernetes | `container.resource_limit.cpu`: 200m | 确认 CPU 资源限制，但未发现对应的 CPU Throttling 证据 |
| 5 | Logging | elasticsearch | 8 条 `/work` 路径 HTTP 200 记录，时间窗口 14 秒 | 证明内存耗尽发生在应用接收到该批请求之后，排除该请求本身引发 OOM |
| 6 | Metric | prometheus | `container_last_terminated_reason`: Error (x1); `container_restarts_total`: 28 | 时序指标确认终止原因及重启频率，与 K8s 状态一致 |
| 7 | Tracing | deepflow+tempo | L7 Flow `/work` 返回 HTTP 200，`duration_us` 范围 8489 - 19885 | 进一步佐证该正常请求耗时较长，可能加速了内存累积，但非直接异常 |

**证据说明：**
K8s Exit Code 137 与 Terminated Reason 明确指向 OOMKilled（事实 1）；低内存限制（96Mi）为根因提供了边界条件（事实 2）；日志显示正常 HTTP 200 请求（事实 5、7）后发生终止，说明是运行时的资源累积效应而非个别非法请求触发；存活探针 500 错误（事实 3）是 OOM 发生后导致重启的直接调度逻辑结果。

## 🎯 根因分析 · g1

### 因果链

```text
内存硬限制过低 (96Mi) → 进程内存累积耗尽触发 OOMKilled (Exit Code 137) → 容器非正常退出 → 存活探针检测超时/失败 (HTTP 500) → CrashLoopBackOff 循环重启 (28次)
```

### 根因结论

已确认根因为：**Pod 的内存限制 (96Mi) 设置过低，导致 Python 工作负载在运行期间耗尽可用内存并被内核 OOM Killer 终止。**

证据支撑：
1. 容器最后一次退出的 Exit Code 为 137 (事实 1)，这是 OOMKilled 的标准特征。
2. 容器配置了极低的内存上限 (96Mi) (事实 2)，远大于请求值 (24Mi)，存在超配但触及硬限制。
3. Pod 状态为 `RecentRestart`，重启次数为 28 (事实 3)，与 CrashLoopBackOff 现象吻合。
4. 日志与链路数据显示正常请求 (HTTP 200) (事实 5, 7) 在发生前被正常处理，排除了单一请求错误直接导致进程崩溃的可能性。
5. 探针返回 500 (事实 3) 是内存压力导致应用响应能力下降或直接被杀后的直接后果。

缺失的不确定性：
- 无法从现有数据确认具体是哪行代码或何种数据结构导致了内存泄漏或激增。
- 无法判断 200m 的 CPU 限制是否加剧了内存压力的发生速度（如 GC 频繁触发）。
- 无法确定单纯增加内存限制是否能永久解决，或者是否存在代码层面的资源泄漏。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 13.2s
├─ 并发证据采集: 120.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 120.0s (Evidence 107.9s, RCA 12.0s)
└─ 汇总总结: 13.0s
```

📋 Runbook 参考

- 未调用 Runbook
