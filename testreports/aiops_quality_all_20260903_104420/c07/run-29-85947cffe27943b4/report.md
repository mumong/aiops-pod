## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-kmfxx处于CrashLoopBackOff状态，容器启动后立即退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 111s (x224 over 51m) kubelet Back-off restarting failed container app` | 确认容器经历了长达 51 分钟的频繁重启，且已进入指数退避状态。 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason: Error`, `container.last_exit_code: 78` | 明确终止原因及退出码，排除 OOMKilled 或探针失败等常见原因。 |
| 3 | Logging | Elasticsearch | `CONFIG_MISSING` (8次, `/work`, HTTP 500, 14:21-14:47) | 日志聚合展示应用启动后持续因配置缺失报错并返回 500。 |
| 4 | Tracing | Deepflow | `GET /work` Flow (9次, `response_code: 500`, 耗时 5260-47772μs) | 追踪层确认流量确实到达 Pod 并被处理，证实应用进程处于“存活但崩溃”的 CrashLoop 状态。 |
| 5 | Tracing | Tempo | `app_span`: `exit_code: 78`, `mode: config_missing_exit`, Trace ID: `65684c...` | 与日志 Fact 3 的 Trace ID 及日志模式一致，直接证实应用因配置缺失主动调用退出接口。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason: CrashLoopBackOff` (value: 1) | 指标状态与 K8s 事件完全一致，确认异常状态持续存在。 |

**证据印证关系：**
证据 1 和 2 提供了宏观的崩溃重启现象和退出码。证据 3（日志）与证据 5（Trace）通过 `exit_code: 78` 和 `CONFIG_MISSING` 模式形成了闭环：应用启动后处理请求（证据 4 证实服务端口可达），遇到缺失配置触发致命错误，记录日志并退出（证据 3、5），导致 Kubernetes 重启容器（证据 1、2）。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-code' 中缺少应用所需的特定配置或环境变量 → 应用处理请求时触发 CONFIG_MISSING 致命错误并返回 500 → 容器进程因未捕获的配置错误崩溃退出（Exit Code 78） → Kubernetes 重启策略触发 CrashLoopBackOff
```

### 根因结论

已确认的根因为：应用启动后在 `/work` 请求中遇到 `CONFIG_MISSING` 致命错误并主动退出（Exit Code 78）。

依据证据 3、4、5，应用进程已成功启动且网络端口可达（Deepflow Flow 确认请求到达且耗时正常），但应用逻辑中检测到关键配置缺失后，无法继续正常运行，导致每次请求均返回 500 并最终触发进程退出。Kubernetes 的自动重启策略因此进入 CrashLoopBackOff 状态。

*注：ConfigMap 'workload-code' 中具体缺失的 key 或应用代码中检查该配置的具体逻辑位置属于未知项，不影响当前故障现象的根因判定。*

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 19.8s
├─ 并发证据采集: 120.6s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 120.6s (Evidence 110.4s, RCA 10.0s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
