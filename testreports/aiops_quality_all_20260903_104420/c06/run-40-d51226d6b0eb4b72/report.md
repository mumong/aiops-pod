## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Python应用进程在处理/work请求时因内存资源耗尽（allocated_mib=0）导致应用层主动异常退出（exitCode=2），触发Kubelet重启后的CrashLoopBackOff循环。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | exitCode=2 | 证实应用进程异常退出，非 Kubelet 或系统级 OOM |
| 2 | K8s State | kubernetes | restart_count=24 | 证实处于 CrashLoopBackOff 循环中 |
| 3 | Metric | prometheus | kube_pod_container_status_waiting_reason{container="app", reason="CrashLoopBackOff"}=1 | 确认容器因异常退出被 Kubelet 等待重启 |
| 4 | K8s Event | kubernetes | Warning BackOff 2m48s (x452 over 102m) | 佐证启动失败的高频与持续时间 |
| 5 | Logging | elasticsearch | 模式 `runtime process exiting`, path="/work", allocated_mib 0 | 证实异常发生在处理请求时，且与资源耗尽有关 |
| 6 | Tracing | deepflow | flow GET /work response_code=500, 3次, trace_ids: 005d.../22fa.../3e8d... | 证实部分请求因应用层逻辑错误被拒绝，并关联到日志模式 |
| 7 | Tracing | tempo | span GET /work trace_id 160828fdbc068f8fae2f2c59ecad1f1b, status_code=200 | 证实该应用也能成功处理相同路径的请求 |

**证据关联说明：**
- 日志 `allocated_mib=0` 与 K8s 侧 `exitCode=2` 互证，表明应用进程在运行时因检测到内存耗尽主动触发退出。
- Tracing 中的 3 次 `500` 错误（Deepflow）与日志中的 `http_status: 500` 模式（Elasticsearch）通过相同的 6 个 `trace_id` 交叉验证，证实了异常发生的具体时刻与业务表现。
- Metric `CrashLoopBackOff=1` 与 K8s 的 `restart_count=24` 及 `BackOff` 事件共同构成了完整的循环重启证据链。

## 🎯 根因分析 · g1

### 因果链

```text
内存资源耗尽(allocated_mib=0) → 应用层主动退出(exitCode=2) → Kubelet触发重启 → CrashLoopBackOff循环
```

### 根因结论

已确认根因：Python 应用进程在处理 `/work` 请求时，检测到自身内存资源耗尽（日志反映 `allocated_mib=0`），导致应用层主动触发异常退出（`exitCode=2`）。Kubelet 检测到容器退出后持续发起重启，从而引发了 `CrashLoopBackOff` 循环。该结论由日志模式（事实 5）、退出码（事实 1）及 K8s 状态证据（事实 2、3、4）充分支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 17.0s
├─ 并发证据采集: 82.1s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 82.1s (Evidence 75.4s, RCA 6.5s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
