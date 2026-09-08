## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Application logic error in /work endpoint causing HTTP 500 and explicit process exit (code 2) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.waiting_reason: `CrashLoopBackOff`; container.last_terminated_reason: `Error`; pod.condition: `ContainersReady=ContainersNotReady` | 确认容器处于反复崩溃重启状态，且非 OOMKill 终止 |
| 2 | K8s State | Kubernetes | container.last_exit_code: `2` | 提供进程退出代码，指向应用逻辑错误而非系统信号崩溃 |
| 3 | Logging | Elasticsearch | pattern: `runtime process exiting`, http_status: `500`, path: `/work`; 记录数: 5 条 | 直接证实应用在处理 `/work` 请求时发生 500 错误并主动退出进程 |
| 4 | Tracing | Deepflow | l7_flow (HTTP GET /work): response_code: `500`; dst_ip: `172.16.104.52`; 出现次数: 3 次 | 从网络层面印证应用对 `/work` 接口的 500 响应事实，与日志记录的时间段及目标 IP 一致 |
| 5 | K8s Event | Kubernetes | event.message: `Warning  BackOff  4m6s (x522 over 118m)  kubelet  Back-off restarting failed container` | 佐证重启频率及长时间未恢复的现状 |
| 6 | Metric | Prometheus | kube_pod_container_status_restarts_total: `27`; kube_pod_container_status_waiting_reason: `1` (CrashLoopBackOff) | 数值层面确认容器已重启 27 次 |

证据链表明，Pod `workload-7679bcf76-jwr8b` 中的 `app` 容器在处理 `/work` 请求时，先返回 500 状态码，随后进程以退出码 2 终止。Kubernetes 的 BackOff 机制导致容器被反复拉起并再次崩溃，形成 CrashLoopBackOff 循环。日志中的 500 错误记录与 Tracing 中的 500 Flow 相互印证，排除了网络或基础设施层面的故障。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码逻辑缺陷 (未捕获异常或逻辑错误) → HTTP 接口 /work 返回 500 并强制进程退出 (Exit 2) → K8s 检测到 Exit 2 且未配置合适的 Liveness Probe 保护或重启策略触发 BackOff → 容器进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为：**Application logic error in /work endpoint causing HTTP 500 and explicit process exit (code 2)**。

证据支持如下：
- **直接证据**：日志事实 `fact-266ef80f4fbc` 等 5 条记录明确显示应用在处理 `/work` 请求时发生 `http_status: 500` 并 `runtime process exiting`。
- **系统行为印证**：K8s 事实 `fact-81b25461b9ca` 显示退出码为 `2`，符合应用程序错误退出的常见模式；事实 `fact-40eee310ff92` 和 `fact-5e88e0b0ff82` 确认了由此引发的 `CrashLoopBackOff` 和 `BackOff` 警告。
- **网络层印证**：Tracing 事实 `fact-9ebeecabfc1a` 等捕获了相同的 500 响应，进一步锁定了故障点位于 `/work` 端点的应用逻辑处理过程中。

目前证据不足以判断具体的代码缺陷类型（如空指针、未捕获异常等），但可以确定故障源头在应用层 `/work` 接口的处理逻辑。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 14.9s
├─ 并发证据采集: 112.8s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 112.8s (Evidence 106.0s, RCA 6.7s)
└─ 汇总总结: 12.9s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
