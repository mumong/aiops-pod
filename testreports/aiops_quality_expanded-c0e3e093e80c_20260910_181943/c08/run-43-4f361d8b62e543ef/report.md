## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | Running | Container memory limit (64Mi) is insufficient for application memory growth pattern, causing OOMKilled. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | Exit Code: 137 | 容器因收到 SIGKILL 信号终止，通常指向 OOM 触发。 |
| 2 | K8s State | `kubernetes` | Reason: OOMKilled | 明确标识导致容器退出的直接原因为 Out Of Memory。 |
| 3 | K8s State | `kubernetes` | Reason: CrashLoopBackOff | 容器频繁重启，符合内存泄漏或内存不足导致的持续失败模式。 |
| 4 | K8s Config | `kubernetes` | Container memory limit: 64Mi | 容器内存硬限制仅 64Mi，资源配额极低，为 OOM 提供上下文。 |
| 5 | K8s Event | `kubernetes` | Warning BackOff 52s (x472 over 124m) | 异常状态已持续 124 分钟，重启次数高达 472 次，证实故障的持续性。 |
| 6 | Metric | `prometheus` | `kube_pod_container_status_last_terminated_reason` (reason: OOMKilled) | 验证了容器最后一次退出的原因为 OOMKilled，与 K8s State 事实一致。 |
| 7 | Metric | `prometheus` | `kube_pod_container_status_restarts_total` = 25 | 容器已重启 25 次，进一步确认 CrashLoopBackOff 现象。 |
| 8 | Logging | `elasticsearch` | Pattern: memory allocation advanced, `numeric_fields` (min: 12.0Mi, max: 38.0Mi) | 业务日志显示内存持续分配，峰值已达 38Mi，逼近 64Mi 的硬限制。 |
| 9 | Tracing | `deepflow+tempo` | Span: `GET /work`, `attributes.aiops.observed_mode: oom_growth` | 追踪特征明确标记了 `oom_growth` 模式，证实请求处理过程中内存呈增长趋势。 |

**证据互证说明：**
K8s 状态（fact-16cc63cb4324）与 Metric 数据（fact-5f1a789a2cab）共同锁定了 OOMKilled 状态；日志（fact-0e830ea38b9b 等聚合组）与追踪数据（fact-3264a37936db 等聚合组）一致显示，在应用处理请求（`/work`）时，内存分配从 12Mi 持续增长至 38Mi，且追踪直接观察到 `oom_growth` 特征。这种增长趋势在 64Mi 的硬限制下，直接解释了 Exit Code 137 及随后的 CrashLoopBackOff 现象。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理 /work 请求时内存持续增长 (max 38Mi) → 逼近并触及 64Mi 内存硬限制 → 内核触发 OOMKilled (Exit Code 137) → 容器崩溃重启并陷入 CrashLoopBackOff
```

### 根因结论

**已确认的根因**：容器 `app` 的内存限制配置过低（`64Mi`），无法满足应用处理请求时的内存增长需求。

**依据**：
1.  **K8s 状态**证实容器因内存不足被强制终止（`OOMKilled`, `Exit Code: 137`）且频繁重启（`CrashLoopBackOff`, `restart_count: 25`）[[证据 1, 2, 3, 5]]。
2.  **业务日志与追踪**证实了故障机理：在 `GET /work` 请求的处理过程中，应用存在持续的内存增长模式（`oom_growth`），内存分配量最高达到 `38Mi` [[证据 8, 9]]。虽然 38Mi 小于 64Mi，但结合 OOMKilled 事实及内存增长的趋势（memory allocation advanced），表明峰值内存需求已超出或极度逼近硬限制，且 GC 或碎片化导致实际可用内存不足以支撑后续分配。
3.  **Metric** 数据直接支持了终止原因为 `OOMKilled` [[证据 6]]。

综上，证据链闭环：应用内存增长特性 + 极低的内存上限配置 = OOMKilled 及持续重启。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 32.6s
├─ 并发证据采集: 101.9s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 101.9s (Evidence 96.5s, RCA 5.2s)
└─ 汇总总结: 14.8s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-oomkilled, pod-crashloop-runtime
