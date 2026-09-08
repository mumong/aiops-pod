## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | Pod workload-79d9f8fd88-bwqhh 持续 CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason=Error`, `container.last_exit_code=137` | 容器异常终止的直接证据 |
| 2 | K8s Event | Kubernetes | `Warning Unhealthy ... Liveness probe failed: HTTP probe failed with statuscode: 500` | 探针返回 500 错误，直接触发容器被杀 |
| 3 | K8s State | Kubernetes | `container.restart_count=16` | 确认处于持续重启循环状态 |
| 4 | Metric | Prometheus | `container_memory_working_set_bytes` (App容器): 首次 15.5 MiB -> 当前 684 KiB，最大值 16 MiB (事实 `fact-c9fdb6f2e3b8`) | 内存始终维持在 15 MiB 低位，未触及 96Mi 限制，排除内存超限 (OOMKilled) 可能 |
| 5 | K8s Config | Kubernetes | `container.resource_limit.memory=96Mi`, `container.resource_request.cpu=20m`, `container.resource_limit.cpu=200m` | 资源配额宽松，非资源争抢所致 |
| 6 | Logging | Elasticsearch | `http_request` 日志模式显示 8 次 `http_status=200` 访问 `/work` 路径 (事实 `fact-70526069318a` 等) | 证实应用内部服务逻辑正常，能成功响应非探针请求 |
| 7 | Tracing | Deepflow/Tempo | Deepflow 显示 `response_code=200` 的 `/work` 流量 (事实 `fact-63a83acff54d` 等)；Tempo 显示 `liveness_fail` 模式且 `http.response.status_code=200` (事实 `fact-41c4768a2028`) | 网络层与链路追踪确认业务请求通畅，但探针路径逻辑被特殊模式干预 |

**证据关系说明：**
1. K8s 事件 (事实 #2) 显示探针收到 500 响应，而日志 (事实 #6) 和追踪 (事实 #7) 均记录其他路径正常响应 200，这证明应用服务本身未崩溃，而是**特定探针请求被有意拦截并返回了 500**。
2. 状态 (事实 #1) 显示 Exit Code 为 137 (SIGKILL)，结合内存指标 (事实 #4) 始终远低于 96Mi 限制，排除了 OOM，确认容器是被系统信号强制终止的，这与探针失败后 kubelet 的行为逻辑一致。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置 FAILURE_MODE=liveness_fail (已验证配置) → Liveness Probe 请求 /health 返回 HTTP 500 (事实 #2) → kubelet 发送 SIGKILL 终止容器 (事实 #1, #2) → 容器 CrashLoopBackOff (事实 #3)
```

### 根因结论

**已确认根因：** 应用运行参数 `FAILURE_MODE=liveness_fail` 导致健康检查接口 (Liveness Probe) 故意返回 HTTP 500 状态码。

**分析：**
kubelet 在执行 Liveness 探测时收到 500 响应，判定容器不健康，随即发送 SIGKILL 信号终止容器进程（表现为事实 #1 中的 `Exit Code 137`）。容器重启后再次触发相同的逻辑，导致 16 次反复重启 (事实 #3)。

**佐证逻辑：**
*   **排除资源故障**：内存指标 (事实 #4) 显示峰值仅 16 MiB，远低于 96Mi 限制，且日志/链路中其他非探针请求均正常返回 200 (事实 #6, #7)，证明非 OOM 或非服务逻辑错误。
*   **确认探针逻辑**：探针返回 500 是唯一能同时解释“容器被杀”和“业务日志正常”的事实 (事实 #2, #6)。

**结论**：该集群现象并非由资源不足或网络故障引起，而是应用配置 (`FAILURE_MODE=liveness_fail`) 主动破坏了 Liveness Probe 的预期行为所致。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 28.6s
├─ 并发证据采集: 104.6s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 104.6s (Evidence 96.0s, RCA 8.5s)
└─ 汇总总结: 14.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
