## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | Liveness Probe失败导致容器被Kubelet Kill |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` | 揭示应用层面对 Liveness 探测的具体失败行为，直接触发后续机制。 |
| 2 | K8s State | Kubernetes | `Container app failed liveness probe, will be restarted` | 记录 Kubelet 判定容器不健康并执行 Kill 的操作事件。 |
| 3 | K8s State | Kubernetes | `Exit Code: 137` | 确认容器进程因收到 SIGKILL 信号而异常终止，符合被 Kubelet 杀死的特征。 |
| 4 | K8s Event | Kubernetes | `Back-off restarting failed container app in pod...` | 展示 Pod 进入反复重启循环（CrashLoopBackOff）的最终表现。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason = 1` (reason: `CrashLoopBackOff`) | 从监控系统侧验证 Pod 当前正处于崩溃重启等待状态。 |
| 6 | Logging | Elasticsearch | 请求完成日志 (HTTP 200, path: `/work`, 时间窗口: 03:16:15 - 03:16:43) | 证明应用在某些请求窗口内处于正常服务状态，说明故障具有间歇性或特定条件触发特征，而非进程挂死。 |
| 7 | Tracing | Deepflow/Tempo | Flow `GET /work` 返回 HTTP 200，耗时 12ms-29ms (时间窗口: 11:03:17 - 11:16:11) | 佐证应用对外提供服务的连通性和基本性能正常，缩小故障为应用层瞬时错误的可能性。 |

**证据关联说明：**
- **K8s Event (#1, #2, #3)** 构建了完整的因果链：应用返回错误 → Kubelet 判定死亡 → 执行 Kill (Exit Code 137)。
- **Metric (#5)** 提供了全局状态的旁证，确认集群层面观察到的是 CrashLoopBackOff 行为。
- **Logging (#6) 与 Tracing (#7)** 展示了应用在某些时间片段内成功处理了 `GET /work` 请求（HTTP 200），这与持续的 Liveness 500 探测失败形成对比，说明应用进程并未完全崩溃，而是针对探测接口或特定执行路径出现了间歇性错误（HTTP 500）。由于缺乏容器内部崩溃原因（如 OOM 或业务逻辑死锁）的证据，根因可锁定为探测失败，但探测失败的具体业务诱因未确认。

## 🎯 根因分析 · g1

### 因果链

```text
应用层间歇性返回 HTTP 500 (由探测接口触发) → Liveness Probe 检测失败 → Kubelet 执行 Kill (Exit Code 137) → Pod 触发 CrashLoopBackOff 重启循环
```

### 根因结论

**已确认的根因：** Liveness Probe 探测失败导致 Kubelet 杀死并重启容器。
- 依据 `fact-955af1c0f3ce`，Kubelet 明确记录了 `Liveness probe failed: HTTP probe failed with statuscode: 500`。
- 依据 `fact-75c6d15c2960` 和 `fact-f526fb3fca6f`，容器的退出码为 `137`，证明容器是被 Kubelet 强制杀死的。
- 依据 `fact-aeb2992655ac`，集群处于反复重启的 `BackOff` 状态。

**证据不足的部分：** 容器应用层为何间歇性返回 500（如资源耗尽、特定业务逻辑错误）缺乏决定性证据。
- 日志 `fact-3d32e6488347` 和 Tracing `fact-420798646af7` 均显示应用在处理普通业务请求（`/work`）时返回了成功的 `HTTP 200`，排除了全进程死锁或永久挂起的可能。
- 系统未提供应用崩溃（OOMKill）或详细内部堆栈的日志，因此无法进一步定位触发 500 的具体应用层诱因。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 27.3s
├─ 并发证据采集: 105.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 105.0s (Evidence 95.6s, RCA 9.2s)
└─ 汇总总结: 14.3s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime
