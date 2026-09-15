## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | 应用 Liveness Probe 端点 `/health` 持续返回 HTTP 500 导致容器被 kubelet SIGKILL (Exit 137) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-761505a26c7e) | 揭示容器启动后，健康检查点持续失败的具体原因 |
| 2 | K8s State | Kubernetes | `last_terminated_reason: Error`, `last_exit_code: 137` (fact-1a896740fd37, fact-b70e5ca7a563) | 确认容器是被强杀终止的，直接对应 SIGKILL 信号特征 |
| 3 | K8s Event | Kubernetes | `Back-off restarting failed container app` (fact-0922ebc4765b) | 证实了系统自动触发的重启保护机制 |
| 4 | K8s Config | Kubernetes | `resource_request.cpu: 20m`, `resource_limit.cpu: 200m`, `resource_limit.memory: 96Mi` (fact-099fa5cc5853, fact-11ccf8d3fb58, fact-53de7b479ce9) | 确认资源请求与限制配置值，供排除资源溢出时参考 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason: CrashLoopBackOff` (fact-f4357d646ba4) | 指标状态印证 Pod 当前正卡在等待重启的循环中 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 31` (fact-18ec3aee2772) | 量化容器在过去一段时间内的崩溃频率 |
| 7 | K8s State | Kubernetes | `Pod Phase: Running`, `Ready: False` (fact-60f0ab235c4a, fact-b158c7879fbc) | 确认 Pod 实例本身存活，但业务并未就绪 |

证据印证：Kubernetes 事件明确指出了 Liveness Probe（`/health` 返回 500）是崩溃的起因，而容器退出的 `Exit Code 137` 是 Linux 系统对 SIGKILL 信号的标准响应，二者结合证实了是外部探针机制强杀了内部容器进程，导致其不断重启并触发 BackOff 限制。日志和追踪数据显示应用在非健康检查路径（`/work`）上 HTTP 200 返回正常，这限定了故障范围仅在健康检查端点或探针配置逻辑上。

## 🎯 根因分析 · g1

```text
应用 Liveness Probe 端点 `/health` 持续返回 HTTP 500 → kubelet 判定容器不健康并发送 SIGKILL 终止进程 (Exit 137) → 容器频繁崩溃重启触发 BackOff 机制 → Pod 处于 CrashLoopBackOff 状态且不可用
```

### 根因结论
**已确认的根因**：应用 Liveness Probe 端点 `/health` 持续返回 HTTP 500 状态码，导致 kubelet 持续判定容器处于“不健康”状态，进而向容器进程发送 SIGKILL 信号强制将其终止（表现为 Exit Code 137）。由于容器不断崩溃重启，最终触发了 Kubernetes 的指数退避重启策略（BackOff），导致 Pod 陷入 CrashLoopBackOff 状态。

**支持事实**：
1. Liveness Probe 失败事件直接指出 `/health` 端点返回 500 (fact-761505a26c7e)。
2. 容器终止退出码为 137，这是典型的被外部信号 (SIGKILL) 杀死的特征 (fact-b70e5ca7a563)。
3. 当前 Pod 等待状态明确为 `CrashLoopBackOff` (fact-f11a844720c8, fact-f4357d646ba4)。

---

## 📊 性能统计

```text
├─ 总耗时: 2.8m
├─ 问题定位: 16.0s
├─ 并发证据采集: 138.7s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 138.7s (Evidence 128.7s, RCA 9.8s)
└─ 汇总总结: 13.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime
