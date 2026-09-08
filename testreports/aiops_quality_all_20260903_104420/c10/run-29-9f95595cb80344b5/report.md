## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | {'type': 'Warning', 'reason': 'BackOff', 'message': 'Warning  BackOff  66s (x328 over 86m)  kubelet  Back-off restarting failed container app in pod workload-79d9f8fd88-sbqvc_aiops-case-10(b1c01c93-0091-4506-bcbd-69cfd75e0f12)'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Events | `message="Warning BackOff ... Back-off restarting failed container app" (x328 over 86m)` | 确认 Pod 进入 CrashLoopBackOff 状态及崩溃持续时间 |
| 2 | K8s State | K8s Events | `message="Exit Code: 137"`, `container.last_terminated_reason="Error"` | 确认进程是被系统信号 (SIGKILL) 强制终止 |
| 3 | K8s Config | K8s Resources | `resource_limit.memory=96Mi` | 提供容器内存硬限制，作为 OOM 判定的基准 |
| 4 | Metric | Prometheus | `container_memory_working_set_bytes` max=18194432.0 (17.36Mi), last=2240512.0 (2.1Mi) | 当前采集到的最新内存值远低于 Limit，未捕获到崩溃瞬间的高水位数据 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 31 | 侧面印证容器经历频繁重启，与 K8s 状态一致 |
| 6 | Logging | Elasticsearch | `log.message="request completed"`, `http_status=200`, `numeric_fields.allocated_mib={min:0, max:0}` (8次) | 证明应用服务在崩溃前的日志记录窗口内处于正常响应状态，未记录 OOM Killer 日志 |
| 7 | Tracing | Tempo/Deepflow | `http.request.method="GET"`, `http.response.status_code=200`, `trace_ids` 正常返回 | 独立于日志的系统级观测，确认崩溃前存在成功的服务调用，非应用逻辑报错 |

**证据链互证说明**：
K8s 的 `Exit Code 137` (证据 2) 是容器被强制终止的确凿证据，通常指向 OOM。然而，Kubernetes 的 BackOff 事件 (证据 1) 说明该进程已在集群中反复重启。由于 Metrics (证据 4) 仅能展示重启后的低水位值（2-17Mi），远低于 Limit (96Mi)，无法直接证实是应用内存越界。与此同时，Logging (证据 6) 和 Tracing (证据 7) 一致表明，应用在崩溃前的运行期间正常处理了 HTTP 请求（Status 200），且没有内部异常日志记录。这种“无报错退出 + 无 OOM 内存峰值记录”的现象，与常规 OOMKilled 的日志输出存在冲突/数据盲区。

## 🎯 根因分析 · g1

### 因果链

```text
容器内进程触发 SIGKILL (Exit Code 137) → Kubernetes 容器运行时终止容器 → 重启间隔指数退避 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

**证据不足**。

现有证据能够确认容器进程因非正常退出码 `137` (SIGKILL) 被终止，进而导致 Pod 进入 `CrashLoopBackOff` (证据 1, 2)。虽然 `137` 退出码常由 OOM Killer 引起，但以下关键决定性事实缺失或处于盲区：
1. **内存峰值数据缺失**：Metric 数据 (证据 4) 显示当前采集到的内存值在 2-17Mi 之间，远低于配置的 `96Mi` Limit (证据 3)。由于重启间隔较长，未能捕获崩溃瞬间的内存峰值。
2. **缺乏 OOM 日志**：Logging (证据 6) 和 Tracing (证据 7) 显示应用崩溃前的运行记录均正常（Status 200），未检测到 OOM 触发时的应用内内存分配异常或系统 OOM Killer 记录（通常需通过 `kubectl logs --previous` 获取，但事实来源中未包含该数据）。

因此，无法确证是应用内存泄漏突破 Limit、宿主机级别强制杀进程（如节点压力），还是 Previous Logs 中缓冲的 OOM 信息未能采集到。确诊需要获取崩溃瞬间的 `Previous Logs` (排查 OOM) 或 `Pod YAML` (排查探针或启动配置)。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 22.4s
├─ 并发证据采集: 87.9s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 87.9s (Evidence 76.2s, RCA 11.5s)
└─ 汇总总结: 14.3s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime, pod-notready-probe-failed
