## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Application configuration missing (CONFIG_MISSING) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `BackOff`：在 44 分钟内 Back-off 重试 175 次重启 Pod `workload-dff5cbc6b-fkzvn` 中的容器 `app` | 确认容器 `app` 处于 CrashLoopBackOff 状态，频繁崩溃 |
| 2 | K8s State | Kubernetes | 退出码 `78` (exit_code)，终止原因为 `Error` | 确认应用启动失败的具体退出信号 |
| 3 | Logging | Elasticsearch | 日志模式：`CONFIG_MISSING` (status 500)，路径 `/work`，8 次重复发生 | 直接指出应用运行期间缺失必要配置，是启动失败的直接原因 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 从 5 增至 12 (8 个样本点，趋势向上) | 量化展示容器在短时间内连续重启，与日志出现时间窗口一致 |
| 5 | Tracing | Deepflow / Tempo | HTTP GET /work 返回 500 (flow_count: 9)，Trace ID `233897f569e70e3ab019024ab2845eb9` | 网络层确认请求因应用内部错误被拒绝，日志与追踪存在 trace_id 关联 |
| 6 | K8s State | Kubernetes | 容器资源限制 `memory_limit: 96Mi`，请求 `memory_request: 24Mi` | 确认 Pod 具备基本计算资源，排除因资源耗尽（OOMKilled）导致的 CrashLoopBackOff |

**证据关联说明：**
- **日志与追踪的关联**：日志中报告的 `CONFIG_MISSING` 错误，在 Deepflow 追踪中表现为 `response_code: 500`。追踪数据明确包含 `trace_ids` 关联，证实了日志中的业务异常被网络工具成功捕获并对应，共同指向同一个失败的请求实例。
- **重启行为的验证**：Kubernetes 的 Event 显示极高频的 `BackOff` (175次)，而 Prometheus 指标 `restarts_total` 在此期间从 5 增加到 12。这种不一致可能源于指标采集时间窗与 Event 观察窗口的差异，但两者都从不同维度证实了容器 `app` 的持续崩溃状态。
- **排除干扰因素**：资源限制（96Mi）充足且退出码非 137 (OOMKilled)，排除资源不足导致的崩溃；日志明确给出了 `CONFIG_MISSING` 的业务错误信息，直接解释了退出码 78 的原因。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动缺失关键配置 (CONFIG_MISSING) → 应用服务初始化失败 (退出码 78) → Kubelet 持续重启 Pod (CrashLoopBackOff) → 用户侧应用访问返回 500 错误，容器无法保持运行
```

### 根因结论

已确认根因为 **应用配置缺失 (CONFIG_MISSING)**。

- **证据支撑**：
  1. **直接业务证据** (编号 3)：日志聚合事实 `pattern` 明确指出 `CONFIG_MISSING`，且 `http_status: 500`，与用户可见现象一致。
  2. **业务行为证据** (编号 5)：追踪数据确认了该错误触发了 HTTP 500 响应，说明应用在运行期间（或启动后的短暂存活期内）确实因配置问题拒绝了请求。
  3. **系统现象** (编号 1, 4)：K8s 的 CrashLoopBackOff 和 Prometheus 的 Restart 计数增长，证实了该应用因配置错误导致进程反复退出，系统不断尝试重启但始终失败。

现有证据足以支撑该根因，无需补充更多数据即可判定应用因配置项缺失导致服务启动失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 15.4s
├─ 并发证据采集: 70.9s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 70.9s (Evidence 65.3s, RCA 5.5s)
└─ 汇总总结: 13.2s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime, pod-oomkilled
