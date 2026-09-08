## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | 应用服务在处理 /work 路径时发生运行时逻辑错误，导致 HTTP 500 响应并强制退出进程 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-06/workload-7679bcf76-w9s9c` 处于 `CrashLoopBackOff`；`app` 容器最后终止原因 `Error`，退出码 2，重启 27 次 | 确认为应用服务异常终止，而非基础设施故障 |
| 2 | K8s Event | Kubernetes | `BackOff` 事件：`Back-off restarting failed container app...`，120分钟内触发 541 次 | 证实应用处于高频重启状态 |
| 3 | Logging | Elasticsearch | 模式 `runtime process exiting`，HTTP 500，路径 `/work`，连续记录 5 次；数值字段 `allocated_mib` 首尾均为 0 | 提供直接的应用逻辑错误证据，内存使用无异常 |
| 4 | Tracing | Deepflow | L7 Flow 聚合：`GET /work` 响应 500 (status 3)，6 次发生，耗时 5266-29145 μs | 从网络层确认了 `/work` 接口的服务侧超时/异常 |
| 5 | Tracing | Tempo | Span `76224ace...`：`GET /work` 返回 HTTP 500，属性 `aiops.observed_mode: runtime_exit` | 从链路层确认请求处理中进程直接退出 |
| 6 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` 显示 `Error`，重启总数 `27` | 独立于 K8s State 的外部观测，验证了状态 |
| 7 | K8s Config | Kubernetes | 资源 Request：CPU `20m`，内存 `24Mi`；Limit：CPU `200m`，内存 `96Mi` | 提供环境基线，配合日志内存占用为 0 可排除资源超限 |

证据间高度印证：Kubernetes 的 `CrashLoopBackOff` 与 Prometheus 的 `Error` 状态一致。Logging 与 Deepflow/Tempo 均精准定位到 `GET /work` 接口返回 `HTTP 500` 且伴随 `runtime_exit`，而内存指标始终为 0 且资源限制充裕，排除了 OOM 可能。

## 🎯 根因分析 · g1

### 因果链

```text
应用服务处理 /work 路径时的运行时逻辑错误 → 进程强制终止（Exit Code 2） → Pod 被 K8s 重启（CrashLoopBackOff） → 用户请求遭遇 HTTP 500 并持续重试失败
```

### 根因结论

根因是 `workload-7679bcf76-w9s9c` 中的 `app` 容器在处理 `GET /work` 请求时发生了运行时逻辑错误。

**证据支撑**：
- **应用异常**：Elasticsearch 日志明确记录了 `http_status: 500` 与 `runtime process exiting` 模式（见证据 #3）；Tempo 链路数据证实了 `aiops.observed_mode: runtime_exit` 且伴随 HTTP 500 响应（见证据 #5）；Deepflow 聚合了 6 次相同的 500 错误 Flow（见证据 #4）。
- **非资源导致**：应用日志中 `allocated_mib` 始终为 0（见证据 #3），结合 Kubernetes 配置（见证据 #7）及 Metric 无 OOM 迹象，证明并非内存限制（Limit 96Mi）或 CPU 不足引发。
- **集群状态**：Kubernetes Event 记录的高频 `BackOff`（见证据 #2）与 K8s 状态 `CrashLoopBackOff` 共同证实了进程反复崩溃重启导致的集群异常表现。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 24.5s
├─ 并发证据采集: 97.1s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 97.1s (Evidence 91.0s, RCA 5.9s)
└─ 汇总总结: 13.1s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
