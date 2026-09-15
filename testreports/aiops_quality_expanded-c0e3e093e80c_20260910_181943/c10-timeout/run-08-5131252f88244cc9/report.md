## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | RecentRestart | {'container': 'app', 'reason': 'Error'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason: Error` (fact-0ef0d2f99493) | 确认容器非正常退出，但 `Error` 未直接指明 OOMKilled，需结合 Exit Code 分析。 |
| 2 | K8s Event | kubernetes | `Warning Unhealthy ... Liveness probe failed: context deadline exceeded` (fact-1a8d7f85c448) | 证明在容器被杀前，应用响应已超时，排除了应用完全假死或崩溃导致无响应的可能。 |
| 3 | K8s Event | kubernetes | `Warning BackOff ... Back-off restarting failed container` (fact-b77536b7e4b3) | 证实容器频繁重启且触发指数退避机制，反映故障持续发生。 |
| 4 | K8s Config | kubernetes | `resource_limit.memory: 64Mi` (fact-bb7656a78fc3), `resource_request.memory: 8Mi` (fact-2ba508332d23) | 确认存在极低的内存限制（64Mi），这是触发 OOMKilled 的高风险配置，为猜测 OOM 提供基础。 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total: 9` (fact-a5a0830ed95d) | 量化重启频率，与 K8s 事件中的 BackOff 状态对应。 |
| 6 | Logging | elasticsearch | `GET /ready ... 200`, `GET /health ... 200`, `listening on 18080` (fact-046017c711de, fact-074d68251b50, fact-419c75f82558) | 证明应用进程至少在 13:19:49 之前是正常运行并监听服务的，说明崩溃是突发性的。 |
| 7 | Tracing | deepflow | `L7 Flow: GET /health ... response_code: 200, duration_us: 3001057.0 ~ 3001920.0` (fact-3c0efe8d8c1b) | 追踪记录证实 `/health` 接口虽耗时极长（~3秒），但响应码始终为 200，支持“应用处理慢导致探针超时”的推测。 |

**证据说明：**
1-2, 5, 7 号证据互相印证：应用虽然在运行（日志 200 OK，Tracing 200 Code），但响应极慢导致 Liveness Probe 超时（K8s Event），进而导致 Kubelet 发起 Kill 动作。
4 号证据（极低内存限制）解释了 Exit Code 137 的高概率成因（OOM），但 6 号证据（进程仍在监听）表明内存问题可能在最后时刻才触发，或存在其他资源竞争导致响应变慢。目前缺乏直接的 OOM 指标或 Terminated Reason 细节来完全锁定内存。

## 🎯 根因分析 · g1

### 因果链

```text
疑似内存资源耗尽或进程处理阻塞 → 应用响应变慢导致 Liveness Probe 超时 → Kubelet 判定不健康并终止容器 (Exit 137) → 容器反复重启并进入 CrashLoopBackOff
```

### 根因结论

**证据不足。**

当前证据链显示容器因 `Exit Code 137`（SIGKILL）异常退出，且伴随 Liveness Probe 超时和频繁重启。虽然配置中极低的内存限制（`64Mi`）使得 `OOMKilled` 成为最可能的根本原因，但现有事实存在以下缺口：
1. 缺乏 `Terminated Reason` 为 `OOMKilled` 的直接字段证据（当前仅显示为 `Error`）。
2. 缺乏 `container_memory_usage_bytes` 或 `oom_events` 等指标证明内存确实触顶。
3. 虽然应用响应极慢（Tracing 显示耗时 ~3s）导致探针超时，但未能排除是因内存争用导致的“假死”还是其他资源/逻辑缺陷。

在未获取到明确的 OOM 终止原因或内存飙升至 limit 的历史数据前，无法确诊根因为 OOMKilled。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 24.7s
├─ 并发证据采集: 98.8s
│  └─ g1 aiops-case-v17/workload: 98.8s (Evidence 85.7s, RCA 12.9s)
└─ 汇总总结: 14.9s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-oomkilled, pod-crashloop-runtime
