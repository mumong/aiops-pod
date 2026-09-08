## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Pod workload-dff5cbc6b-fkzvn 因 CrashLoopBackOff 处于不健康状态（虽然最新快照显示 Running，但处于 Error 状态且重启 20 次） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 4m38s (x332 over 79m) ... Back-off restarting failed container app` (fact-9252f0ce3f49) | 确认应用处于 CrashLoopBackOff 状态，频繁重启 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason: Error`, `exit_code: 78` (fact-25cb2293207c, fact-285542cd3e88) | 容器异常退出并返回特定错误码 |
| 3 | Logging | Elasticsearch | Pattern: `http_request` (500), `CONFIG_MISSING`, path: `/work` (9 occurrences, e.g., fact-13e2ada463ab) | 揭示应用内部报错的具体原因：配置项缺失 |
| 4 | Tracing | Tempo | Span: `GET /work`, `http.response.status_code: 500`, `aiops.observed_mode: config_missing_exit` (fact-056e308a9210) | 验证了应用因配置缺失主动终止请求的逻辑模式 |
| 5 | Tracing | Deepflow | Flow: `GET /work`, `response_code: 500`, count: 11 (fact-6c1f1b9f5c2c) | 跨网络层面确认请求失败并伴有应用内部错误 |
| 6 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason: 1` (label: reason=Error) (fact-14dc67259d54) | 佐证 K8s 层面的异常终止状态 |
| 7 | K8s State | Kubernetes | `container.restart_count: 20` (fact-2d9abfd3a71d) | 量化了重启频度 |

**证据关联说明：**
K8s 侧的 `BackOff` 事件与 `Exit Code 78` 定义了崩溃现象。日志中的 `CONFIG_MISSING` 提供了根本原因，Tempo 的 Span `aiops.observed_mode: config_missing_exit` 精确关联了应用层的行为模式，二者在证据链上形成闭环。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动配置键缺失 (CONFIG_MISSING) → 应用服务在处理请求时抛出异常并退出 (Exit Code 78) → Kubelet 检测到容器异常退出并触发重启 → 重启失败累计导致 CrashLoopBackOff
```

### 根因结论

**已确认的根因：应用启动脚本中配置键缺失 (CONFIG_MISSING)。**

该配置项缺失导致应用进程在运行（处理请求时）抛出异常并退出，Kubernetes 检测到容器异常退出（Exit Code 78）后自动进行重启，由于进程持续崩溃最终触发了 `CrashLoopBackOff`。

支持证据：
- **应用层证据**：日志显示 9 次 HTTP 请求因 `CONFIG_MISSING` 返回 500 错误 (fact-13e2ada463ab)；Trace 明确标记 `aiops.observed_mode: config_missing_exit` (fact-056e308a9210)。
- **系统层证据**：容器终止原因为 `Error` (fact-25cb2293207c)，退出码为 `78` (fact-285542cd3e88)，且 K8s Event 显示大量 `BackOff` (fact-9252f0ce3f49)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 16.5s
├─ 并发证据采集: 75.6s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 75.6s (Evidence 64.5s, RCA 11.0s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
