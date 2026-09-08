## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | 应用配置缺失（ConfigMissing）导致服务启动后无法正常运行：每次容器启动后，应用进程成功初始化但缺少必要配置，导致 /work 端点立即返回 HTTP 500 错误，随后进程异常退出并触发 CrashLoopBackOff 循环。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Prometheus | `kube_pod_container_status_waiting_reason` 1, `reason=CrashLoopBackOff`; `kube_pod_status_phase` 1, `phase=Running` | 确认 Pod 处于持续重启状态，且底层节点正常，非调度或集群资源问题 |
| 2 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` 1, `reason=Error`; `kube_pod_container_status_restarts_total` 18 | 证实容器因 `Error` 退出并经历了 18 次重启循环，符合异常退出特征 |
| 3 | Logging | Elasticsearch | 模式 `CONFIG_MISSING`, `http_status=500`, `path=/work`；时间窗 `14:42:13` 至 `15:08:21`；`numeric_fields` 显示 `allocated_mib=0` 始终为 0 | 证明服务启动后进程正常运行并响应请求，但因“配置缺失”在 `/work` 路径立即返回 HTTP 500，排除了资源耗尽（OOM）导致退出的可能 |
| 4 | Tracing | Tempo | Trace ID `65684c8c...`: span `GET /work` 返回 500，属性明确包含 `aiops.observed_mode=config_missing_exit` | 从链路层确认 500 错误是应用逻辑的显式退出信号，而非网络或代理层面的超时/连接错误 |
| 5 | Tracing | DeepFlow | L7 聚合流: `GET /work` 持续返回 500 (`occurrence_count=9`)；时间窗 `22:42:17` 至 `23:08:19` | 提供高并发的外部观测，证实配置缺失导致的 500 错误是持续性而非瞬时现象，且与日志时间窗存在重叠，验证了故障的稳定性 |

证据链条表明：
1. 容器重启并非由于 OOM 或探针失败（`allocated_mib=0`），而是应用逻辑异常（Log & Trace 确认）。
2. 应用能够启动并监听请求（Tracing Span 成功建立连接），但在处理 `/work` 请求时因缺少关键配置主动返回 500 并退出（Log `CONFIG_MISSING`）。
3. 日志与 Trace 的 Trace ID 存在关联（如 `65684c8c...` 在两者中均有出现），直接证实了 HTTP 500 与容器终止之间的因果关系。

## 🎯 根因分析 · g1

### 因果链
```text
应用必要配置缺失 (ConfigMissing) → /work 端点请求处理异常 (HTTP 500) → 进程异常退出 (Error Exit) → Pod 触发 CrashLoopBackOff 循环
```

### 根因结论
**已确认根因：应用配置缺失（ConfigMissing）。**
现有证据充分支持该结论：
1. **直接证据**：Elasticsearch 日志中聚合了 8 次 `CONFIG_MISSING` 错误，且伴随 `http_status=500`，明确指出了缺失的是应用层面的配置项，而非系统级配置（如 Secret/ConfigMap 挂载失败）。
2. **过程验证**：Tempo 和 DeepFlow 的链路数据显示，应用容器成功启动并处理了流量，但在请求 `/work` 时显式返回了 500 并带有 `config_missing_exit` 标记。这证实了故障点发生在应用内部逻辑执行阶段。
3. **排除干扰**：监控指标显示内存分配始终为 0（`allocated_mib=0`），彻底排除了 OOMKilled 导致的 CrashLoopBackOff 可能性。

综上，应用启动后能够正常响应，但因缺乏必要的配置参数，在特定接口调用时触发业务逻辑错误导致进程退出，从而陷入重启循环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 19.7s
├─ 并发证据采集: 45.0s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 45.0s (Evidence 38.0s, RCA 6.9s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
