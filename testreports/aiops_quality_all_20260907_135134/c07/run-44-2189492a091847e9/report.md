## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | Error | 应用配置缺失 (CONFIG_MISSING) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `BackOff  5m52s (x377 over 90m)  Back-off restarting failed container app` | 直接展示应用长期处于 CrashLoopBackOff 状态，启动反复失败。 |
| 2 | K8s State | kubernetes | `container.waiting_message: back-off 5m0s restarting failed container=app` | 确认 pod 当前因退出码异常而持续处于重启退避等待中。 |
| 3 | K8s State | kubernetes | `container.last_terminated_reason: Error, last_exit_code: 78` | 应用容器以特定非零退出码 78 终止，属于业务逻辑层报错而非资源耗尽导致的 SIGKILL。 |
| 4 | Logging | elasticsearch | `pattern: CONFIG_MISSING, http_status: 500, path: /work, service: aiops-lab-workload` (发生 10 次, time: 2026-09-07T15:34:03Z ~ 2026-09-07T16:05:27Z) | 日志明确记录请求在 `/work` 路径因缺少应用配置而返回 500 错误，解释了启动/服务失败的业务根因。 |
| 5 | Tracing | deepflow+tempo | `span: GET /work, service: aiops-lab-workload, status_code: 500, attributes: aiops.observed_mode: config_missing_exit` (trace_id: 435ddc9f7062bac6badf52854f8152a6) | 与日志模式关联，通过 Trace 属性确认为配置缺失触发的应用退出机制，而非网络或底层故障。 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total: 22` | 量化证实了容器在短时间内发生了 22 次重启，印证了日志观察到的持续性失败。 |

证据互证说明：
1. Kubernetes 层面记录的高频重启（Event x377, Metric 22次）及非正常退出码 78，表明容器启动即失败。
2. 应用层日志（CONFIG_MISSING）与 Trace（config_missing_exit）提供了失败的确切业务原因，说明容器并非因 OOM 或 Crash 意外退出，而是程序启动阶段因读取配置失败主动报错退出。
3. 资源指标（CPU 200m/0.2 core, Memory 96Mi）未显示超限额，排除了资源约束导致 CrashLoopBackOff 的可能。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置项缺失 (在 /work 路径下) → 容器初始化/启动阶段读取配置失败 (exit code 78) → 进程立即退出并触发 K8s BackOff 机制 → Pod 长期处于 CrashLoopBackOff 状态，服务不可用
```

### 根因结论

已确认的根因为**应用配置缺失 (CONFIG_MISSING)**。

*   **证据支撑**：
    *   **日志维度**：日志明确报告 `CONFIG_MISSING` 错误，且发生在 `/work` 路径下，直接关联到应用启动时的配置加载逻辑。
    *   **追踪维度**：Trace 数据中的属性 `aiops.observed_mode: config_missing_exit` 与日志互相印证，表明应用以特定的业务异常模式退出。
    *   **系统状态维度**：退出码为 78（通常为特定应用退出码），配合 `CrashLoopBackOff` 状态，确认了这种非随机、高可重复性的启动失败模式正是导致当前 Pod 无法运行的直接原因。

*   **局限性/未知项**：虽然明确了是“配置缺失”导致，但输入事实（及诊断元数据）指出尚无法确定 `ConfigMap workload-code` 中具体**缺失了哪个配置项名称**，也无法还原触发该异常的**具体代码逻辑分支**。但这已足以解释当前的集群异常状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 25.1s
├─ 并发证据采集: 77.0s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 77.0s (Evidence 70.0s, RCA 6.9s)
└─ 汇总总结: 13.8s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-oomkilled
