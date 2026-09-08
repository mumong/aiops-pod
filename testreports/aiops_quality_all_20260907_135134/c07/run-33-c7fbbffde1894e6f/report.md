## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Pod 'app' 容器启动并执行服务时，因缺失必要的配置项（日志报错 CONFIG_MISSING, HTTP 500, 退出码 78）导致应用反复崩溃重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason=CrashLoopBackOff`, `container.last_terminated_reason=Error`, `restart_count=18`, `exit_code=78` (fact-22ed30824a28, fact-3ea0938b1e60, fact-76a13201f31f, fact-32ad0e89b76d) | 确定 Pod 处于反复崩溃重启状态，且退出原因被标记为 Error，提供具体的退出码。 |
| 2 | K8s Event | Kubernetes | `Warning BackOff ... Back-off restarting failed container app` (fact-f0faf7332eb7) | 记录容器重启频率和退避行为，印证启动失败机制。 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason[reason="CrashLoopBackOff"]=1`, `kube_pod_container_status_last_terminated_reason[reason="Error"]=1`, `restart_total=18` (fact-620e8224faad, fact-2fc176e6c8d2, fact-03d83427bd6f) | 独立监控指标再次确认了 CrashLoopBackOff 状态、错误终止原因及重启次数 18 次，与 K8s 状态吻合。 |
| 4 | Logging | Elasticsearch | `pattern="CONFIG_MISSING"`, `http_status=500`, `time_range="2026-09-07T15:23:32" to "15:44:22"` (fact-015df69f68ff 等) | 提供具体的业务侧日志证据，显示应用启动或运行期间抛出致命错误 "CONFIG_MISSING" 并返回 HTTP 500，是崩溃的明确前置事件。 |
| 5 | Tracing | Deepflow (Flow) | `HTTP GET /work response_code=500`, `dst_ip=172.16.104.7` (fact-3d2b10bfbad0 等) | 网络流量记录显示指向 Pod IP (172.16.104.7) 的 GET /work 请求均返回 500，佐证了应用层在请求处理时的持续故障。 |
| 6 | Tracing | Tempo (Span) | `trace_id=7ed664affe6fdd8e75610015d3c8e3a3`, `http.response.status_code=500`, `attributes.aiops.observed_mode=config_missing_exit` (fact-251f255919dc) | 应用内部 Span 明确记录了 `config_missing_exit` 模式及 500 状态码，与日志中的 `CONFIG_MISSING` 模式精确对齐。 |

证据链闭环印证：Kubernetes 的 `CrashLoopBackOff` 状态与 Prometheus 的监控指标一致，表明 Pod 持续失败。Elasticsearch 的 `CONFIG_MISSING` 日志（15:23-15:44 期间）与 Deepflow/Tempo 中 HTTP 500 响应及 `config_missing_exit` 追踪模式相互补充，共同指向应用因配置缺失（`exit_code=78`）而主动退出。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码/配置缺失必要配置项 (CONFIG_MISSING) → 应用启动后处理请求抛出致命错误并退出 (exitCode=78) → Kubernetes 重启策略触发连续重启 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因为 **应用缺失必要配置项**。
应用启动并执行服务时，遇到配置缺失（`CONFIG_MISSING`），导致处理请求时抛出致命错误并返回 HTTP 500，最终以退出码 78 退出容器。Kubernetes 的重启策略触发了 18 次重启，最终导致 Pod 进入 `CrashLoopBackOff` 状态。
*   支撑证据：`CONFIG_MISSING` 日志 (fact-015df69f68ff 等)，`config_missing_exit` 追踪模式 (fact-251f255919dc)，HTTP 500 流量记录 (fact-3d2b10bfbad0 等)，以及 `CrashLoopBackOff` 状态和 `exit_code=78` (fact-22ed30824a28, fact-32ad0e89b76d)。

缺失的确定性事实包括 **具体的缺失配置变量名或配置文件路径**，以及挂载的 ConfigMap `workload-code` 中具体的内容缺失情况，这些细节无法从当前的日志和指标事实中直接解析。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 15.5s
├─ 并发证据采集: 61.5s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 61.5s (Evidence 53.7s, RCA 7.6s)
└─ 汇总总结: 16.3s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
