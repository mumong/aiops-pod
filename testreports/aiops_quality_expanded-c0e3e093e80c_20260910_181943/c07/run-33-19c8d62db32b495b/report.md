## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod workload-dff5cbc6b-sjvxl 持续处于 CrashLoopBackOff 状态，表现为反复启动失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod 状态：Running；容器重启计数：16 次 (fact-871c965ec127, fact-ccc1958eeed3) | 确认存在反复重启的持续故障现象 |
| 2 | K8s Event | kubernetes | Warning BackOff 警告，58分钟内发生 242 次，提示 Back-off restarting failed container app (fact-0892812c5269) | 确认异常组现象：CrashLoopBackOff |
| 3 | K8s State | kubernetes | 容器 app 上次终止原因：Error，退出码：78 (fact-fd3580eaba1c, fact-522bc03f8c9c) | 提供应用崩溃的直接退出状态证据 |
| 4 | K8s Config | kubernetes | 容器内存限制 96Mi，CPU 限制 200m (fact-0dada20b969a, fact-36b839a819ef) | 资源上下文信息，用于排除内存 OOM (结合日志中 allocated_mib 为 0 的情况) |
| 5 | Logging | elasticsearch | 错误日志模式：http_request [level: error] message: CONFIG_MISSING, http_status: 500, path: /work (fact-0dc98f941e4c, fact-2c24f58804e0 等) | 直接指向根因：应用因配置缺失导致内部错误并退出 |
| 6 | Logging | elasticsearch | 数值指标 allocated_mib 在 21:02:53 至 21:23:51 期间 min/max 均为 0 (fact-0dc98f941e4c) | 排除资源耗尽导致 OOM 的可能性 |
| 7 | Tracing | deepflow | HTTP Flow 聚合：GET /work -> 500 (3次响应)，src_ip: 172.16.104.8 -> dst_ip: 172.16.104.63 (fact-239265a728e1 等) | 佐证服务对外暴露 500 错误 |
| 8 | Tracing | tempo | Span GET /work: aiops.observed_mode=config_missing_exit, 关联 trace_id: 55c07e8b117659114ccbae9c7f582db0 (fact-543b1502ed84) | 通过跨工具关联，从底层追踪视角确认了 CONFIG_MISSING 的具体执行模式 |

**证据说明：**
Kubernetes 侧的 `BackOff` 事件与 16 次重启计数确认了 CrashLoopBackOff 现象。Logging 侧聚合日志明确指出错误原因为 `CONFIG_MISSING`，且 `allocated_mib` 为 0 排除了内存 OOM 导致的非正常退出。Tracing 侧的 Span 数据（fact-543b1502ed84）与 Logging 侧的 trace_id（`55c07e8b117659114ccbae9c7f582db0`）精确匹配，从分布式追踪链路角度再次印证了“应用处理请求时因配置缺失异常退出”的事实。日志中记录的时间范围与 K8s 的 BackOff 发生时间窗口一致。

## 🎯 根因分析 · g1

### 因果链

```text
应用运行环境缺失必要配置 → 进程处理 HTTP 请求时触发 CONFIG_MISSING 错误并退出 → 容器以退出码 78 终止 → Kubelet 触发 BackOff 重启机制导致 CrashLoopBackOff
```

### 根因结论

已确认根因为**应用进程因缺少必需配置导致处理请求时抛出异常并终止（Exit Code 78）**，进而触发 Kubernetes 的 CrashLoopBackOff 重启机制。

这一结论由以下证据共同支撑：
1.  **Kubernetes 现象**：Pod 处于 Running 状态，但容器 `app` 因 Error 退出 16 次，并触发 BackOff 重启事件（#1, #2, #3）。
2.  **直接错误原因**：ELK 日志聚合显示，每次循环中均记录有 `CONFIG_MISSING` 错误，且伴随 HTTP 500 状态码（#5）。
3.  **排除资源限制**：日志指标 `allocated_mib` 始终为 0，且容器内存限制为 96Mi，排除了 OOM 导致退出的可能（#4, #6）。
4.  **跨维度关联**：Tempo 的 Trace 数据中明确记录了 `aiops.observed_mode=config_missing_exit`，且通过 trace_id `55c07e8b117659114ccbae9c7f582db0` 与日志中的记录完全匹配（#8, #5），确证了应用崩溃的直接机制是配置缺失引发的逻辑异常。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 24.5s
├─ 并发证据采集: 88.6s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 88.6s (Evidence 77.8s, RCA 10.6s)
└─ 汇总总结: 17.1s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
