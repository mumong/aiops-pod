## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod workload-7679bcf76-n5vp8 因应用进程异常退出导致 CrashLoopBackOff 并反复重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Back-off restarting failed container app in pod workload-7679bcf76-n5vp8_aiops-case-06` (x497 over 113m) | 确认 Pod 进入 CrashLoopBackOff 且处于频繁重启循环中 |
| 2 | K8s State | Pod | `container.last_terminated_reason`: Error, `last_exit_code`: 2, `restart_count`: 26 | 确认容器以非零退出码 2 异常终止，且已重启多次 |
| 3 | Logging | elasticsearch | 模式 `runtime process exiting` (HTTP 500, path `/work`), 4次重复出现 | 直接指向进程内部的运行时错误导致主动退出机制被触发 |
| 4 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason`: Error (1), `kube_pod_container_status_restarts_total`: 26 | 从监控侧独立确认容器最近一次终止原因为 Error 且重启总数达到 26 次 |
| 5 | Tracing | tempo/deepflow | Flow: `GET /work` -> 500; `GET /work` -> 200; Span: `aiops.observed_mode: runtime_exit` | 提供请求级视角：应用处理 `/work` 请求期间发生内部异常，导致响应异常或进程直接退出 |

**证据综合说明**：
1. Kubernetes 层面（事实 1、2、4）与日志层面（事实 3）高度一致：Pod 因应用进程错误退出而反复重启，且日志明确记录了导致退出的模式为 `runtime process exiting`。
2. 追踪层面（事实 5）展示了具体的请求流（`GET /work`）与异常状态（500 或 `runtime_exit`），印证了该 Pod 在处理特定业务请求时存在不稳定性，进一步支持“应用层逻辑故障”导致进程退出的结论。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码在请求处理期间触发运行时异常 (Logging: runtime process exiting) → 应用进程执行主动退出逻辑 (Logging, Tracing: runtime_exit) → kubelet 检测到容器非零退出码 (exit_code: 2) 并触发重启策略 (K8s: restart_count=26) → 频繁重启导致 Pod 进入 CrashLoopBackOff 状态 (K8s: BackOff event)
```

### 根因结论

**已确认根因**：工作负载 `workload-7679bcf76-n5vp8` 中的应用程序在处理 `GET /work` 请求时发生运行时错误，触发了进程内部的退出机制（`reason: runtime process exiting`），从而导致容器以退出码 2 终止。Kubernetes 根据重启策略自动拉取并重启该容器，但由于应用代码层面的错误未被修复，导致容器陷入反复退出的循环，最终使 Pod 状态进入 `CrashLoopBackOff`。
*支撑证据*：
- 日志：`runtime process exiting` 模式 (事实 3)
- 追踪：`aiops.observed_mode: runtime_exit` 且关联 `/work` 请求 (事实 5)
- 容器状态：`last_terminated_reason: Error` 与 `last_exit_code: 2` (事实 2, 4)

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 21.4s
├─ 并发证据采集: 71.8s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 71.8s (Evidence 62.7s, RCA 9.0s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
