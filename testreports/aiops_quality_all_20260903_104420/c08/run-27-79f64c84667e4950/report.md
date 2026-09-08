## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | Running | Pod workload-5c9c7b6489-fl85h 处于 CrashLoopBackOff 状态，容器 app 频繁重启（16次） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason`: reason="OOMKilled" (fact-1) | 证实容器因资源耗尽被内核强制终止 |
| 2 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 从 6.0 增至 16.0 (fact-1) | 证实 Pod 处于 CrashLoopBackOff 状态，容器频繁重启 |
| 3 | Metric | prometheus | `container_memory_working_set_bytes`: 峰值达 58146816 bytes (约 55.4 MiB) (fact-1) | 确认内存使用量远超正常水平，达到终止阈值附近 |
| 4 | Logging | elasticsearch | 日志模式 "memory allocation advanced" 累积 8 次，allocated_mib 从 10 增至 42 (fact-1) | 提供内存增长轨迹，证明应用内部存在持续的内存分配行为 |
| 5 | Tracing | tempo | Trace: GET /work (200)，属性 `aiops.observed_mode: oom_growth` (fact-1) | 关联到具体的 /work 接口调用，并标注了内存增长模式 |
| 6 | Tracing | deepflow | L7 Flow: GET /work 9 次，响应 200 (fact-1) | 证实该接口被持续调用，且均正常返回，未发生应用层错误 |

证据表明：应用通过 `/work` 接口持续处理请求，伴随日志中 `allocated_mib` 的逐次增加和 Metric 中内存使用的不断攀升，最终导致系统触发 OOMKilled 机制。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码处理 /work 请求时持续分配内存（allocated_mib 从 10 增至 42） → 内存使用量持续增长耗尽容器资源 → 内核 OOM Killer 终止容器进程 (OOMKilled) → Pod 因容器崩溃进入 CrashLoopBackOff 状态（重启 16 次）
```

### 根因结论

已确认根因为 **应用处理 /work 请求时存在内存泄漏**。

具体证据链如下：
- 内存泄漏机制：日志显示每次 "memory allocation advanced" 事件后，`allocated_mib` 持续递增（从 10 到 42），且 Tracing 数据明确标记该模式为 `oom_growth`。
- 资源耗尽结果：`container_memory_working_set_bytes` 持续攀升至峰值 58146816 bytes，最终触发 `last_terminated_reason: OOMKilled`。
- 业务表现：由于泄漏导致频繁重启，Pod 状态变为 `CrashLoopBackOff`。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 20.0s
├─ 并发证据采集: 105.6s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 105.6s (Evidence 93.6s, RCA 11.9s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-oomkilled
