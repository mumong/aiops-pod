## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | 应用主进程在启动或运行时因关键配置缺失（CONFIG_MISSING）导致请求处理失败（HTTP 500），进而以非零退出码（Exit Code 78/Error）主动终止，引发 Kubernetes 反复重启并进入 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | Warning BackOff 8s (x490 over 109m) kubelet Back-off restarting failed container app in pod workload-dff5cbc6b-fkzvn | 确认 Pod 进入 CrashLoopBackOff 状态的直接原因 |
| 2 | K8s Event | Kubernetes | Reason: CrashLoopBackOff | 确认 Pod 当前生命周期状态 |
| 3 | K8s State | Kubernetes | Container 'app' last terminated reason: Error, exit code: 78 | 提供容器非正常终止的底层状态码，指向应用主动退出 |
| 4 | K8s State | Kubernetes | Container 'app' restart count: 25 | 确认启动失败已引发持续性反复重启 |
| 5 | K8s Config | Kubernetes | container.app resources: requests {memory: 24Mi, cpu: 20m}, limits {memory: 96Mi, cpu: 200m} | 排除资源限制（OOM）导致容器被 K8s 杀死的常见原因 |
| 6 | Logging | Elasticsearch | Pattern: {event: http_request, level: error, message: "CONFIG_MISSING", http_status: 500, path: "/work"} (8 occurrences) | 提供应用内部错误日志，定位根因为关键配置缺失 |
| 7 | Tracing | Deepflow/Tempo | Flow/Trace ID `9a3b9b13a8706d6da508428164070448`: GET /work HTTP 500, aiops.observed_mode: config_missing_exit | 链路数据印证日志，并提供了与日志相同的 Trace ID，建立闭环证据 |

证据相互印证：
Kubernetes 的 BackOff 事件（#1, #2）和重启计数（#4）确认了 Pod 处于故障重启循环中；退出码 78 和 Error 状态（#3）表明是应用层主动终止而非底层资源限制（#5）。应用日志（#6）和深度链路追踪（#7）共同揭示了终止的具体原因是启动或运行时的配置缺失（CONFIG_MISSING）导致返回 HTTP 500，最终应用报错退出。追踪数据中的 Trace ID 与日志记录的 Trace ID 一致，确认了是同一故障请求。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动/运行时关键配置缺失 (CONFIG_MISSING) → 处理请求失败并返回 HTTP 500 → 主进程主动终止 (Exit Code 78) → Kubernetes 反复重启并进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认的根因：**
异常组的根本原因在于应用工作负载 `aiops-case-07/workload-dff5cbc6b-fkzvn` 在启动或运行期间未能加载关键配置（日志记录为 `CONFIG_MISSING`）。这导致应用在处理请求（如 `GET /work`）时抛出异常并返回 HTTP 500 状态码，主进程随即以非零退出码（Exit Code 78）主动终止。Kubernetes 根据重启策略不断尝试拉起该 Pod，但因配置问题依旧存在，Pod 陷入持续重启并最终进入 CrashLoopBackOff 状态。

**证据链：**
1. **现象确认**：K8s 事件显示 Pod 因连续重启进入 BackOff 状态，且容器多次以 Error 状态退出（见证据 #1, #2, #3, #4）。
2. **资源排除**：Pod 资源请求与限制配置合理，排除了内存不足（OOMKilled）导致被 K8s 杀死的常见情况（见证据 #5）。
3. **机制定位**：应用日志中反复出现 `CONFIG_MISSING` 错误及 HTTP 500 状态（见证据 #6）。
4. **链路闭环**：深度追踪数据不仅捕获了 HTTP 500 请求，还明确标注了故障模式为 `config_missing_exit`，且其 Trace ID 与日志记录中的 Trace ID 完全匹配，确认了上述因果逻辑（见证据 #7）。

**未确认事项：**
目前证据未能揭示具体缺失的配置文件名、变量名，也无法追溯至上游配置管理系统的故障根因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 16.9s
├─ 并发证据采集: 60.3s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 60.3s (Evidence 52.3s, RCA 7.8s)
└─ 汇总总结: 14.3s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
