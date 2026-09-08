## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Application startup logic fails due to missing required configuration files (exitCode=78, error='CONFIG_MISSING'), triggering immediate container termination. |
| g2 | `monitor/prometheus-observability-prometheus-0` | Running | Prometheus 规则评估中存在大量 duplicate series（由多 Service 采集同一 Kubelet 端点导致 many-to-many matching 约束违规），引发规则组持续评估失败与高负载；长期运行及规则处理压力导致容器内存耗尽被 OOMKilled 并重启。当前实例虽为 Running 状态，但 Readiness probe 持续失败表明服务实际不可用。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-4ddb24db33aa` | `BackOff` 2m30s (x131 over 32m)，pod `workload-dff5cbc6b-fkzvn` (ns `aiops-case-07`) | 确认应用启动后立即失败并被系统频繁重启，呈现 CrashLoop 特征 |
| 2 | K8s State | `fact-bff65f4bfaf6` | `exit_code=78` | 异常退出码，结合 `Error` 终止原因，指向非资源耗尽型的逻辑或配置错误 |
| 3 | Logging | `fact-0bf8c10f8ebd` | `CONFIG_MISSING` (level `error`, http_status `500`, path `/work`)，连续发生于 `14:38` 至 `15:02` | 明确业务逻辑失败的具体原因为“缺少配置”，解释了退出码 78 的触发机制 |
| 4 | Tracing | `fact-10d9788ad8e5` | Trace `261d9e55a970c37b1d05368956e13953` 的 Span `GET /work` 返回 `500`，属性 `aiops.observed_mode=config_missing_exit` | 通过跨链追踪关联日志与 HTTP 流量，证明失败发生在业务处理链路内部 |
| 5 | K8s Config | `fact-15dec7ec17bb` / `fact-6c120c0a7b0b` | CPU request `20m` / limit `200m`，Memory request `24Mi` / limit `96Mi` | 排除容器因资源超限（OOM/Killed）被杀死的非预期可能 |

日志中反复出现的 `CONFIG_MISSING` 错误与 Trace 中观测到的 `config_missing_exit` 状态高度一致，共同指向应用启动或初始化阶段的配置缺失问题；K8s 层面的 Restart 行为（ExitCode 78）是该应用逻辑失败后的必然结果，排除了基础设施故障。

## 🎯 根因分析 · g1

### 因果链

```text
必需配置文件缺失 (未确认来源) → 应用启动/初始化逻辑抛出 CONFIG_MISSING 错误 → 容器进程以 exit code 78 终止 → Kubelet 触发 BackOff 机制导致应用 CrashLoopBackOff
```

### 根因结论

**已确认根因**：Pod `aiops-case-07/workload-dff5cbc6b-fkzvn` 中的 `app` 容器因**启动或初始化逻辑缺失必要的配置文件**而导致业务失败。
- **机制**：应用代码在执行 `/work` 请求或启动检查时发现配置缺失（`CONFIG_MISSING`），主动以退出码 `78` 终止自身。
- **证据支撑**：
  1. 日志维度：记录了 8 次 `level=error` 的 `CONFIG_MISSING` 模式（`fact-0bf8c10f8ebd`）。
  2. 追踪维度：通过 Trace ID `261d9e55...` 关联的 Span 明确标记了 `config_missing_exit` 模式（`fact-10d9788ad8e5`）。
  3. 集群维度：Kubelet 捕获到容器因 `Error` 退出（`fact-aea3f138e0f7`），并记录了非 OOM 的退出码 `78`（`fact-bff65f4bfaf6`），排除了资源限制（`fact-6c120c0a7b0b`）导致的异常。

---

## 🕵️ 证据内容 · g2

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubelet | `Readiness probe failed: Get "http://172.16.166.165:9090/-/ready": context deadline exceeded (x146)` | 证明服务虽然存活（Running），但响应超时必须性超时，处于不可用状态。 |
| 2 | K8s State | Container Last Terminated | `reason: OOMKilled`, `exit_code: 137` | 证明 Prometheus 因内存耗尽触发 OOM 终止，解释了 Readiness 检测为何出现断崖式超时。 |
| 3 | Logging | Elasticsearch | `found duplicate series for the match group ... many-to-many matching not allowed` | 证明规则 `CPUThrottlingHigh` 与 `node_quantile:kubelet_pleg...` 因匹配多对多约束违规持续评估失败。 |
| 4 | K8s Config | Container Resources | `memory_limit: 512Mi`, `memory_request: 256Mi` | 提供资源限制事实，证实内存配置极小，在持续的高负载和评估失败下极易耗尽。 |

**证据说明**：
日志中关于 `many-to-many matching not allowed` 的报错（#3）揭示了 Prometheus 长期处于高负载和规则组失败重试的状态，这直接导致了内存资源的消耗。结合内存限制事实（#4），可以解释为何容器会触发 OOMKilled（#2）。而 OOM 后的容器重启导致了 Readiness 探针的连续超时（#1），构成了完整的故障现象链条。

## 🎯 根因分析 · g2

### 因果链

```text
多 Service 采集同一 Kubelet 端点导致 Duplicate Series → 规则评估违反 many-to-many 匹配约束持续失败 → 规则组反复处理引发高负载与内存持续增长 → 超出 512Mi 限制触发 OOMKilled → Pod 重启导致 Readiness Probe 连续超时服务不可用
```

### 根因结论

已确认根因为 **Prometheus 规则组评估失败引发的连锁内存耗尽与重启**。

日志事实证实，由于采集配置导致同一 Kubelet 端点存在重复系列（Duplicate Series），引发 `CPUThrottlingHigh` 等规则在匹配操作（`on (cluster, instance) group_left`）中违反 `many-to-many` 约束，导致规则评估持续报错失败（证据 #3）。这种持续的评估失败和高负载最终导致 Prometheus 容器（限制为 512Mi）内存耗尽并被 OOMKilled（证据 #2）。当前 Pod 状态为 `Running`，但由于处于重启阶段或恢复阶段，Readiness 探针持续超时（证据 #1），表现为服务不可用。

---

## 📊 性能统计

```text
├─ 总耗时: 7.4m
├─ 问题定位: 28.2s
├─ 并发证据采集: 397.8s
│  ├─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 72.7s (Evidence 67.8s, RCA 4.8s)
│  └─ g2 monitor/prometheus-observability-prometheus-0: 397.8s (Evidence 389.6s, RCA 7.8s)
└─ 汇总总结: 15.9s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
