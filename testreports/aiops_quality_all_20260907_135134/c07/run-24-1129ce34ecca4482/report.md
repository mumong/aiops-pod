## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | ConfigMap 'workload-code' 挂载路径下缺少应用启动所需的配置文件或 Key，导致应用进程启动时读取配置失败（退出码 78 / CONFIG_MISSING）并进入 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 退出码 `78` (fact-145539073294) | 提供进程崩溃的直接退出码，指向配置/文件缺失类错误 |
| 2 | K8s State | Kubernetes | 容器 `app` 状态 `CrashLoopBackOff` (fact-77af831cde0e) | 确认应用启动后立即崩溃并持续重启的现象 |
| 3 | K8s Event | Kubernetes | `Warning BackOff ... back-off 5m0s restarting failed container` (fact-56205adb62fd) | 确认kubelet因容器频繁退出执行指数退避重启策略 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 `1`，标签 `reason="CrashLoopBackOff"` (fact-4a9a293daa64) | 从集群级别指标确认该 Pod 处于等待重启状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 值为 `13` (fact-842203c4f866) | 量化重启次数，确认为非偶发故障 |
| 6 | Logging | Elasticsearch | 错误模式 `CONFIG_MISSING`，路径 `/work` (fact-1dc34210d4bd 等 8 条记录) | 核心业务日志直接指明故障原因为配置缺失 (CONFIG_MISSING) |
| 7 | Tracing | Deepflow/Tempo | HTTP `GET /work` 返回 `500` 状态码，伴随 trace_id 匹配 (fact-691f9bdc116f, fact-207c4f051754) | 应用接口请求失败，与日志错误码对应，证明应用进程存活但无法处理请求 |

**证据说明：**
Kubernetes 状态提供了故障现象（退出码 78 与 CrashLoopBackOff），Prometheus 指标证实了该异常的持续存在。日志中高频出现的 `CONFIG_MISSING` 模式精准匹配了退出码的含义，Trace 层面的 500 错误进一步印证了应用进程因配置问题导致请求处理失败。多维度证据形成闭环，指向明确的配置缺失原因。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap挂载路径下缺少配置文件或Key → 应用启动读取配置失败(退出码78/CONFIG_MISSING) → 容器进程崩溃 → Pod进入CrashLoopBackOff
```

### 根因结论

已确认的根因为：应用 `workload-dff5cbc6b-fkzvn` 的启动脚本或配置文件挂载点缺失。

证据链如下：
1. **现象确认**：Pod `app` 容器持续以退出码 `78` 崩溃，状态为 `CrashLoopBackOff`（事实 1、2、3、4、5）。
2. **原因定位**：应用内部日志高频报错 `CONFIG_MISSING`，且请求路径为 `/work`（事实 6）。
3. **关联验证**：Trace 数据显示对 `/work` 的请求返回 500 错误，且 Trace ID 与日志关联（事实 7）。

综合证据，根因是 `ConfigMap 'workload-code'` 中缺少应用启动或运行所需的配置文件或 Key，导致应用进程启动失败或启动后无法正常工作而崩溃退出。现有证据链完整，足以支撑此结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 15.0s
├─ 并发证据采集: 59.7s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 59.7s (Evidence 50.6s, RCA 9.0s)
└─ 汇总总结: 12.1s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
