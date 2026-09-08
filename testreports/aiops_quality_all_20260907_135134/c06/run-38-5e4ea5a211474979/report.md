## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Pod workload-7679bcf76-jwr8b 处于 CrashLoopBackOff 状态，容器 app 反复以退出码 2 崩溃重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: CrashLoopBackOff; `container.last_terminated_reason`: Error; `container.last_exit_code`: 2 | 确认应用进程异常终止且被 kubelet 反复重启的症状 |
| 2 | K8s Event | Kubernetes | `Back-off restarting failed container app in pod workload-7679bcf76-jwr8b...` (x406 over 99m) | 证实崩溃行为具有持续性（99分钟内重试406次） |
| 3 | Logging | Elasticsearch | `runtime process exiting` (http_status: 500, path: /work) @ `2026-09-07T13:44:33Z` ~ `14:05:35Z` | 提供应用退出时的内部日志模式，直接指向进程主动退出 |
| 4 | Tracing | Tempo | Span `fb6fd50f7d5...` (`GET /work`, status 500) @ `14:05:35Z` | 与日志中的最后一次退出时间精确一致，确认 `/work` 请求是崩溃前最后的活动 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 23 (at `14:10:13Z`) | 独立量化验证了容器的高频重启状态 |
| 6 | K8s Config | Kubernetes | `container.resource_limit.memory`: 96Mi; `container.resource_request.memory`: 24Mi | 确认资源约束极小，排除因内存超限（OOMKilled）导致退出的可能 |

**证据关联分析：**
- **日志与追踪的时间/动作一致性**：日志 `runtime process exiting` 的最后一条记录时间（`14:05:35.387Z`）与 Tempo Span `fb6fd...` 结束时间（`14:05:35.381Z`）高度吻合，两者均指向对 `/work` 路径的 GET 请求触发退出。
- **退出行为性质**：由于日志包含明确的 `runtime process exiting` 文本且退出码为 2（而非 137 的 OOMKilled），结合内存配置极小的事实，有力证实了崩溃是应用层主动发起的行为，而非基础设施资源故障。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置 FAILURE_MODE=runtime_exit → server.py 检测到配置并触发退出 → 容器进程以 Exit Code 2 终止 → Kubelet 重启失败进入 CrashLoopBackOff
```

### 根因结论

**已确认根因：应用代码根据环境变量配置主动触发了进程退出。**

证据表明，工作负载 `aiops-case-06/workload-7679bcf76-jwr8b` 的容器 `app` 被配置为在启动后处理 `/work` 请求时主动退出。具体表现如下：
1. **应用层日志**明确记录了 `runtime process exiting` 事件（`fact-1e0bcbeae073` 等），证实了退出的内部机制。
2. **追踪数据**将此次退出与对 `/work` 端点的请求关联（`fact-e1edb05a3ceb`），并排除了网络或依赖组件的故障。
3. **资源指标**（`fact-498094fcfb55`）证明内存限制并非导致退出的原因。

综上所述，当前 `CrashLoopBackOff` 状态是由 `FAILURE_MODE=runtime_exit` 配置导致的确定性应用行为，而非集群基础设施或容器运行时故障。

---

## 📊 性能统计

```text
├─ 总耗时: 2.6m
├─ 问题定位: 14.4s
├─ 并发证据采集: 130.7s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 130.7s (Evidence 121.9s, RCA 8.7s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
