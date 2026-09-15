## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | {'message': 'k8s.v1.cni.cncf.io/network-status:'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.last_exit_code` | Exit Code: 137 (fact-ba879e498b69, fact-ca42f483cb08) | 确认容器进程近期因 SIGKILL 终止 |
| 2 | K8s Event | `Unhealthy` | Readiness: "connection refused" | 探针收到连接拒绝，直接触发重启 |
| 3 | K8s Event | `Unhealthy` | Liveness: "context deadline exceeded (Client.Timeout exceeded...)" | 探针响应超时，判定应用假死 |
| 4 | Metric | `kube_pod_container_status_last_terminated_reason` | "Error" (fact-b1831eff4f18) | 独立指标印证 K8s 状态记录的 Error 退出原因 |
| 5 | K8s Config | `container.resource_limit` | CPU: 200m, Memory: 64Mi (fact-7f764a698cb5) | 基础资源限制配置，提供分析终止背景 |
| 6 | Tracing | `L7 Flow` | GET /health: response_code=200, duration_us: 3001057-3001920 (fact-3c0efe8d8c1b) | 存在耗时约 3s 的延迟但返回 200 的流量记录 |
| 7 | Logging | `Log Message` | GET /health HTTP/1.1" 200 - (fact-4aa66c8574b0) | 应用自身日志显示 HTTP 接口成功处理了请求 |

**证据矛盾与印证：**
1-4 号证据一致指向容器经历了异常退出（Exit 137）及健康检查失败。但 6-7 号证据存在冲突：Tracing 显示 `/health` 请求返回 200（尽管耗时约 3s），应用日志也记录成功，这与 3 号证据中 Liveness Probe 报出的 "deadline exceeded"（通常暗示连接或响应超时）存在时序或状态矛盾，无法直接证明进程假死或网络阻断。

## 🎯 根因分析 · g1

### 因果链

```text
容器进程异常终止（exit_code=137） → 健康检查失败（Liveness probe timeout 与 Readiness connection refused） → CrashLoopBackOff
```
*注：健康检查失败的直接原因（进程假死 vs 网络丢包/延迟）因证据冲突标记为“未确认”。*

### 根因结论

**证据不足。**

虽然退出码 137 高度提示 OOMKiller 或内核级 SIGKILL，但当前的探针行为（Timeout/Connection Refused）与应用日志及链路追踪（返回 200 OK）存在直接矛盾。在没有 `containerOOM` 事件或 `OOMScoreAdj` 记录的情况下，无法确认 137 的具体触发源；同时，也无法确定是容器在极短时间内崩溃导致探针超时，还是存在导致探针超时的底层网络问题。缺少决定性的 OOM 或资源压力证据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 19.8s
├─ 并发证据采集: 64.0s
│  └─ g1 aiops-case-v17/workload: 64.0s (Evidence 52.4s, RCA 11.5s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-oomkilled, pod-crashloop-runtime
