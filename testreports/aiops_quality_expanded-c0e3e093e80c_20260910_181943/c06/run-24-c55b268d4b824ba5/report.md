## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | 应用代码在请求处理逻辑中存在运行时异常（exitCode=2），导致进程直接退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container=app, exit_code=2 | 容器异常退出的直接退出码 |
| 2 | K8s State | kubernetes | status=CrashLoopBackOff, restarting=15 | 容器进程进入重启循环的症状 |
| 3 | K8s Event | kubernetes | Warning BackOff 4m20s (x226 over 54m) | 持续且频率增加的重启失败警告 |
| 4 | K8s Config | kubernetes | cpu_limit=200m, memory_limit=96Mi | 资源限制配置，排除硬性资源超量限制 |
| 5 | Logging | elasticsearch | error: http_status=500, message="runtime process exiting", path="/work" | 明确标记运行时进程退出的错误日志模式 |
| 6 | Tracing | deepflow+tempo | span: GET /work, response_code=500, aiops.observed_mode="runtime_exit" | 网络流量与日志 trace_id 关联，确认 500 伴随进程退出 |

**证据关联与印证：**
- K8s 状态（证据 1, 2）中的 `exit_code=2` 直接对应日志（证据 5）和 Tracing（证据 6）中 `/work` 路径的 500 错误。
- Tracing 明确观测到 `observed_mode="runtime_exit"`，且其 `trace_id` 与日志中的 `trace_ids` 完全匹配，证明 500 响应是进程崩溃前的最后一次网络请求，而非网络波动导致。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码 /work 端点处理逻辑缺陷 → 触发运行时异常 (exitCode=2) → 容器进程直接崩溃退出 → 集群执行 CrashLoopBackOff 重启策略
```

### 根因结论

已确认根因为：**应用代码在请求处理逻辑中存在运行时异常**。

该异常（`exitCode=2`）导致进程直接退出，被 Kubernetes 判定为 Error 并触发重启。由于退出原因并非资源耗尽（日志中 allocated_mib 恒为 0），且重启策略（CrashLoopBackOff）生效，导致 Pod 处于不可用状态。K8s 事件、日志错误和 Tracing 异常模式在同一个请求路径 `/work` 上完全吻合，排除了基础设施或配置层面的干扰。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 20.5s
├─ 并发证据采集: 60.0s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 60.0s (Evidence 52.5s, RCA 7.3s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
