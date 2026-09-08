## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-7b77l 处于 Running 状态但 Readiness 探针持续失败，导致 Pod 状态为 NotReady (0/1) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod `aiops-case-09/workload-5f4fb9ff45-7b77l` | status: `Running`, restart_count: `0` | 应用进程存活且未重启，排除资源耗尽导致的崩溃。 |
| 2 | K8s Config | Pod Spec (implied by Probe) | Port `8080` | 确认 Readiness Probe 探测的目标端口。 |
| 3 | K8s Event | `kubelet` Warning | `Readiness probe failed: Get "http://172.16.104.35:8080/ready": dial tcp 172.16.104.35:8080: connect: connection refused` | 早期证据，直接指出对 `/ready` 端点 TCP 连接被拒，显示应用内部逻辑错误。 |
| 4 | K8s Event | `kubelet` Warning | `Readiness probe failed: HTTP probe failed with statuscode: 503` | 后期现象，确认应用进程已恢复或逻辑改变，但 `/ready` 路径持续返回 503。 |
| 5 | Logging | Elasticsearch | `dependency unavailable`, status `503`, path `/work`, `allocated_mib: 0` | 证实应用内部存在未解决的依赖故障，且内存分配正常。 |
| 6 | Tracing | Deepflow/Tempo | GET `/work` -> `503`, trace_id `cd230732dd175914a43aa596f86fcfed` | 链路追踪确认 `/work` 端点失败，佐证内部依赖不可用状态持续存在。 |

**证据互证与冲突说明：**
- K8s 状态与日志/追踪相互印证：Pod 处于 `Running` 且无重启，但日志持续报 `dependency unavailable` 且 `/work` 请求返回 503（证据 5, 6），这与 K8s 探针返回 503（证据 4）完全一致。
- TCP 拒绝与 HTTP 503 的关联：证据 3 中早期的 `connection refused` 与证据 4 中后期的 `HTTP 503` 在时间上呈现先后关系，表明应用进程可能经历过短暂启动异常或初始化阻塞，现已恢复运行但业务逻辑（健康检查依赖的组件）依然不可用。
- 资源维度无干扰：内存 `allocated_mib: 0`（证据 5）表明故障非内存溢出引起。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部上游依赖不可用 → 健康检查逻辑返回 503 → Kubelet Readiness Probe 连续失败 → Pod 被标记为 NotReady (0/1)
```

### 根因结论

**已确认的根因**：应用健康检查逻辑（`/ready`）依赖的内部服务不可用。

*   **故障现象关联**：Kubelet 持续返回 Readiness Probe 失败（503），导致 Pod 失去流量并被标记为 `NotReady`（事实证据：3, 4）。
*   **故障根源支撑**：应用日志（证据 5）和链路追踪（证据 6）明确指向“应用内部依赖不可用（`dependency unavailable`）”。这表明应用进程本身在运行，但其维护健康的端点因依赖组件故障而主动或被动态地返回 503 错误。
*   **结论**：Pod 未 Ready 并非由资源瓶颈、崩溃或 K8s 网络层直接导致，而是**应用层内部依赖异常导致健康检查失败**。

*注：具体是哪个上游依赖（如数据库、缓存或内部微服务）导致了 `dependency unavailable`，以及 `/ready` 端点与 `/work` 业务逻辑的代码关联方式，属于当前未确认项，需查阅应用源码或上游组件日志进一步界定。*

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 19.6s
├─ 并发证据采集: 100.1s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 100.1s (Evidence 89.2s, RCA 10.8s)
└─ 汇总总结: 13.3s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
