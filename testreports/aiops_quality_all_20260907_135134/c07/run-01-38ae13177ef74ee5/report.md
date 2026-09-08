## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | Error | Pod workload-dff5cbc6b-fkzvn 处于 CrashLoopBackOff 状态，容器 app 反复以 Exit Code 78 失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Warning  BackOff 1s (x6 over 89s) ... Back-off restarting failed container app in pod workload-dff5cbc6b-fkzvn` | 直接证明容器已陷入重启循环，且退避时间已达 40s |
| 2 | K8s State | `kubelet` | `container.last_exit_code: 78`, `container.waiting_reason: CrashLoopBackOff` | 确认当前容器处于 CrashLoopBackOff 等待状态，退出码固定 |
| 3 | Logging | `elasticsearch` | `CONFIG_MISSING` (发生 8 次, 含 trace_id: `b3559561ac9acd05071836e31ce2b090`) | 发现导致应用启动/运行失败的明确业务异常日志 |
| 4 | Tracing | `tempo` | Span `GET /work`, status `500`, attribute `aiops.observed_mode: config_missing_exit` (trace_id: `b3559561ac9acd05071836e31ce2b090`) | 与日志 Trace ID 匹配，证明进程在 `/work` 路径处理中因配置缺失直接返回 500 |
| 5 | Tracing | `deepflow` | L7 Flow: `GET /work` → `500`, dst_ip: `172.16.104.7`, 累计 10 次 | 从流量层确认 Pod IP 为 172.16.104.7 的容器频繁接收并报错 500 请求 |

**证据总结：**
Kubernetes 指标与事件 (证据 1、2) 提供了 CrashLoopBackOff 和固定 Exit Code 78 的终止状态。Logging (证据 3) 和 Tracing (证据 4) 通过 `trace_id: b3559561ac9acd05071836e31ce2b090` 直接关联，确证了应用内部因为 `CONFIG_MISSING` 抛出错误并退出。Tracing 流量层数据 (证据 5) 进一步佐证了该 Pod 处于持续接收请求但频繁返回 500 的故障态。

## 🎯 根因分析 · g1

### 因果链

```text
应用缺失关键配置项 (证据 3、4) → 启动/运行时处理 /work 请求抛出 CONFIG_MISSING 错误 (证据 4) → 进程以 Exit Code 78 异常退出 (证据 2) → Kubernetes 触发 CrashLoopBackOff 重启循环 (证据 1)
```

### 根因结论

已确认的根因为应用因 `CONFIG_MISSING` 导致进程启动或运行失败并反复退出。
应用代码（或其所依赖的 ConfigMap `workload-code`）中缺失关键配置项，导致应用在接收请求（如 `/work`）时立即抛出内部错误并返回 HTTP 500，最终进程以非 0 退出码（78）结束。Kubernetes 检测到进程持续退出后，触发指数退避策略进入 `CrashLoopBackOff` 状态。

具体缺失的配置键名未在事实中提供。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 23.8s
├─ 并发证据采集: 93.4s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 93.4s (Evidence 82.2s, RCA 10.9s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
