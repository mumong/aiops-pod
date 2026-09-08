## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | {'type': 'Warning', 'reason': 'Unhealthy', 'message': 'Warning  Unhealthy  2m26s (x69 over 97m)   kubelet  Liveness probe failed: HTTP probe failed with statuscode: 500'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-30c7c5d00712, x69 over 97m) | 证明容器在运行期间对外部探测请求返回了服务内部错误。 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason`: Error, `container.last_exit_code`: 137 (fact-18245b3fa498) | 表明容器进程被强制终止，退出码 137 通常对应 SIGKILL 信号。 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (CrashLoopBackOff), `restarts_total` = 34 (fact-2283f5efc00e, fact-a474d6619727) | 确认容器因反复崩溃进入重启循环状态，但缺乏趋势变化细节。 |
| 4 | Logging | Elasticsearch | `/work` 路径 http_status: 200 (8 occurrences, fact-088a111e57aa, trace_ids: a2d2b4c5494b06f254ff4504f72b49ef...) | 显示应用在某些正常请求中处理成功，但日志未提供崩溃瞬间的报错堆栈或资源告警。 |
| 5 | Tracing | Deepflow/Tempo | `GET /work` response_code: 200, duration: 16-19ms (fact-5d3d89ebabb0, trace_id: 50db7a03ff9f0c293f7a2dfeb50042c9) | 关联日志中的成功请求链路，证明 Pod 在部分时段具备处理能力，未发生全面挂死。 |
| 6 | K8s Config | Kubernetes | Memory limit: 96Mi, Memory request: 24Mi (fact-0eb65e072b87, fact-fd8d04113f98) | 提供了容器内存硬限制的具体数值，是评估 137 退出码是否由 OOM 引起的基础事实。 |

证据 1、2、3 共同证实了“服务异常（500）导致存活探针失败，进而引发容器反复崩溃（137/Restart）”的表象链。证据 4、5 显示应用在特定请求路径上能完成 200 OK 响应，证明应用进程并未完全僵死，与 500 错误及 137 退出码并存，说明故障可能是间歇性的或特定负载下触发的资源耗尽。

## 🎯 根因分析 · g1

### 因果链

```text
未确认的决定性原因（如内存超限或外部信号） → 进程收到 SIGKILL 信号 → 容器退出码 137 → Liveness 探针因服务不可用或状态异常返回 500/失败 → 触发 CrashLoopBackOff
```

### 根因结论

证据不足。

虽然容器退出码 137 强烈暗示进程被强制终止（通常是 OOMKilled 或被节点驱逐），但现有证据无法确诊具体原因：
1. **缺乏 OOM 决定证据**：Prometheus 指标未返回 `OOMKilled` 状态标记（fact-2658d75fc51c），无法确认是否为内存超限导致。
2. **外部 Kill 可能性**：存在其他节点进程或外部 Kill 信号导致 137 退出的可能性，但当前日志和链路中未记录相关的底层系统事件。
3. **服务状态矛盾**：存在 200 OK 的成功响应（fact-088a111e57aa, fact-5d3d89ebabb0），但存活探针却报 500（fact-30c7c5d00712），这表明故障可能发生在应用初始化资源竞争、特定高负载路径，或探针配置与业务逻辑不匹配，需要缺失的 Pod YAML 定义和完整崩溃日志来进一步区分。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 14.1s
├─ 并发证据采集: 74.9s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 74.9s (Evidence 66.6s, RCA 8.2s)
└─ 汇总总结: 14.1s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
