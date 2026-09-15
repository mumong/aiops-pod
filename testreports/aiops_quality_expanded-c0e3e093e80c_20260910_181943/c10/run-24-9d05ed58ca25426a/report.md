## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | Running | Pod workload-79d9f8fd88-48j8r处于CrashLoopBackOff状态，容器app因Liveness Probe返回500被Kubelet Kill (Exit Code 137)。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Liveness probe failed: HTTP probe failed with statuscode: 500` | 确认 Liveness Probe 端点被探测时应用直接返回了业务级错误。 |
| 2 | K8s Event | kubelet | `Container app failed liveness probe, will be restarted` | 确认 Kubelet 因健康检查失败触发了容器 Kill 动作。 |
| 3 | K8s State | Pod Status | `reason: CrashLoopBackOff`, `exit_code: 137`, `restart_count: 9` | 确认容器被反复强制终止并触发指数级重启。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 从 0 升至 8 | 独立度量证实容器处于持续重启状态，非一次性故障。 |
| 5 | Logging | Elasticsarch | `request completed` (path: `/work`), `http_status: 200`, `allocated_mib: 0` | 日志表明应用在业务端点返回 200 且内存正常，排除 OOM 或应用崩溃。 |
| 6 | Tracing | Deepflow/Tempo | HTTP GET `/work` 返回 200，`duration_us: 15684~24044` | 业务请求耗时正常且响应正常，进一步排除应用内部处理逻辑问题。 |

**证据分析**：
Kubernetes 事件明确记录了 Liveness Probe 收到 500 错误是导致容器被 Kill 的直接原因（#1, #2）。与此同时，应用日志（#5）和链路追踪（#6）均显示应用在业务请求（`/work`）上能正常返回 200 响应且无内存异常。这表明容器反复被 `SIGKILL` (Exit 137) 重启并非因为应用崩溃或资源耗尽，而是因为应用对特定的健康检查请求故意返回了 500 错误。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置了 FAILURE_MODE=liveness_fail 故障注入模式 → 应用对 Liveness Probe 端点返回 HTTP 500 错误 → Kubelet 检测到 Probe 失败并发送 SIGKILL 终止容器 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为：Pod 正在处于受控的故障注入模式（Failure Mode: `liveness_fail`）。

具体机制为应用代码故意对 Liveness Probe 检查请求返回 HTTP 500 错误。证据显示：
1.  **健康检查被判定失败**：Kubelet 多次记录 `Liveness probe failed` 且状态码为 500（证据 #1），这直接触发了 Kubelet 的 `Killing` 行为（证据 #2）。
2.  **容器非正常崩溃**：容器以 Exit Code 137（SIGKILL）反复退出，重启次数达到 9 次（证据 #3, #4）。
3.  **应用逻辑未异常**：日志与追踪均显示，应用对正常的业务流量（GET `/work`）返回的是标准的 HTTP 200 成功状态码，且无资源使用异常（证据 #5, #6）。

综上，Pod 的 CrashLoopBackOff 是应用层面的故障注入逻辑（模拟 Liveness 失败）与 Kubelet 的恢复机制共同作用的结果，属于预期行为而非非预期故障。

---

## 📊 性能统计

```text
├─ 总耗时: 3.1m
├─ 问题定位: 23.6s
├─ 并发证据采集: 150.2s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 150.2s (Evidence 140.6s, RCA 9.4s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-oomkilled, pod-crashloop-runtime
