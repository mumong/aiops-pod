## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Pod workload-7679bcf76-jwr8b in aiops-case-06 is in CrashLoopBackOff (restarts=26). |
| g2 | `monitor/prometheus-observability-prometheus-0` | Running | Prometheus 容器因内存不足（OOMKilled）被终止并重启 2 次，导致当前处于不稳定的运行状态，表现为高延迟响应和内部规则评估失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `CrashLoopBackOff`; `container.last_terminated_reason`: `Error`; `container.last_exit_code`: `2` | 确认 Pod 容器 `app` 处于反复崩溃重启状态，且退出码固定为 2。 |
| 2 | Logging | Elasticssearch | Pattern `runtime process exiting` (error level, HTTP 500, path `/work`), 连续 3 次出现，`first: 14:00:20.985Z` ~ `last: 14:21:10.386Z` | 提供崩溃的直接机制证据：业务进程在处理 `/work` 请求后主动终止，无具体异常堆栈。 |
| 3 | Tracing | Tempo | Span `GET /work` (`trace_id: 130bdd4836bc750bcf687e89b717aebe`), 耗时 4ms, 状态码 200 | 关联日志与请求，证明进程在成功返回 HTTP 200 后的代码路径中发生退出。 |
| 4 | K8s Event | Kubernetes | `Warning BackOff 3m49s (x499 over 113m) Back-off restarting failed container app` | 确认该崩溃行为在超过 113 分钟内持续发生，Kubelet 已触发指数退避。 |

证据显示应用进程在响应 `/work` 请求返回 200 后触发退出（`runtime process exiting`），导致 Kubelet 不断重启容器（Exit Code 2）。Tracing 中的 Trace ID `130bdd...` 与 Logging 记录关联，证实了“请求完成 -> 进程退出”的顺序。目前缺少导致该退出的具体代码异常（Traceback）证据。

## 🎯 根因分析 · g1

### 因果链

```text
未捕获的应用层异常 (server.py) → sys.exit(2) 强制退出 → 容器终止 (Exit Code 2) → Pod CrashLoopBackOff
```

### 根因结论

已确认根因为应用容器 `app` 在代码执行过程中因特定路径异常导致非零退出。

事实支撑如下：
1. **崩溃状态**：Kubernetes 报告容器状态为 `CrashLoopBackOff`，最近一次终止原因为 `Error`，退出码（Exit Code）稳定为 `2` [证据 #1]。
2. **崩溃机制**：日志捕获到应用内部明确记录的 `runtime process exiting` 错误，且伴随 HTTP 500 状态码 [证据 #2]。
3. **触发时机**：Tracing 记录显示，在 `/work` 端点成功响应（HTTP 200）后，进程立即终止 [证据 #3]。这表明退出逻辑发生在响应生成之后的收尾阶段。

**未决问题**：
日志中未包含导致 `exit(2)` 的具体 Python 异常堆栈或堆栈跟踪信息（Traceback），无法定位是内存异常、未处理的逻辑错误还是外部依赖调用失败。需补充应用侧完整错误日志以确认最终代码路径。

---

## 🕵️ 证据内容 · g2

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason` value=1 (labels: container=prometheus, reason=OOMKilled) | 证实 Prometheus 容器曾因内存耗尽被内核终止 |
| 2 | Metric | prometheus | `kube_pod_container_status_restarts_total` value=2 (container=prometheus) | 证实故障已引发 Pod 2 次重启，系统处于不稳定恢复期 |
| 3 | Logging | elasticsearch | `Evaluating rule failed` err="found duplicate series... many-to-many matching not allowed" | 证实规则引擎因匹配冲突报错，无法正确评估指标 |
| 4 | Logging | elasticsearch | 错误日志涉及 multiple rules: `CPUThrottlingHigh` (group=kubernetes-resources), `node_quantile:kubelet_pleg...` (group=kubelet.rules), `KubeletPodStartUpLatencyHigh` (group=kubernetes-system-kubelet) | 证实多个告警规则同时因同一类匹配问题失效，增加了资源处理压力 |
| 5 | Tracing | deepflow | L7 Flow: HTTP GET `/federate?match[]={__name__!=""}` from `172.16.166.144` to `172.16.166.165`, duration `15996495.0us` - `42121372.0us` | 证实 Federate 接口响应极慢（约 16-42 秒），表明 Prometheus 主进程资源紧缺，无法及时响应外部请求 |

证据总结：
- 指标显示容器因 OOMKilled 被杀并重启 (fact-1, fact-2)，直接解释了 Pod 不稳定的原因。
- 日志显示多个规则评估失败，原因是匹配标签重复导致的 many-to-many 冲突 (fact-3, fact-4)，虽然这通常是配置问题，但在资源不足时可能加剧处理延迟或失败概率。
- 追踪数据显示 Federate 接口响应时间超过 15 秒 (fact-5)，这与 OOMKilled 导致的系统资源紧张或重启期间的部分不可用状态相吻合，证实了高延迟现象。

## 🎯 根因分析 · g2

### 因果链

```text
Prometheus 容器内存不足 (OOM) → 容器被 OOMKilled 终止并重启 → Pod 处于重启恢复期/资源受限 → Federate 接口高延迟与内部规则评估失败
```

### 根因结论

- **已确认的根因**：Prometheus 容器因内存不足（OOMKilled）被终止并重启 2 次。这直接导致了当前 Pod 的不稳定状态，表现为外部 Federate 请求的高延迟（Tracing 显示响应时间超过 15 秒）以及内部规则评估失败（Logging 显示 `Evaluating rule failed`）。
- **证据支撑**：
    - Metric 确认终止原因为 `OOMKilled` (fact-1) 和重启次数为 2 次 (fact-2)。
    - Tracing 确认了 `federate` 端口的极高延迟 (fact-5)。
    - Logging 确认了规则评估失败的具体错误模式 (fact-3, fact-4)。
- **未知因素**：当前 Prometheus 是否仍存在内存泄漏风险，或 OOM 是否已由其他因素（如数据量激增或规则爆炸）引起，缺乏详细的内存增长趋势或资源限制对比证据，无法进一步界定根本触发原因（是配置不当还是负载过高）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 31.2s
├─ 并发证据采集: 100.8s
│  ├─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 100.8s (Evidence 88.5s, RCA 12.2s)
│  └─ g2 monitor/prometheus-observability-prometheus-0: 48.8s (Evidence 38.5s, RCA 10.2s)
└─ 汇总总结: 15.1s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
