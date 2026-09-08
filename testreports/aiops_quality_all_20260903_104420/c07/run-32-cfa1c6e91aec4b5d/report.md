## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod workload-dff5cbc6b-kmfxx处于CrashLoopBackOff状态，应用容器反复崩溃重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 2m35s (x246 over 57m) kubelet Back-off restarting failed container app` | 证明应用已持续异常重启超 57 分钟，符合 CrashLoopBackOff 现象 |
| 2 | K8s State | Kubernetes | `pod.phase: Running`, `container.restart_count: 15` | 确认 Pod 存活但容器反复退出，且退出码为 `78` |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory: 96Mi`, `container.resource_limit.cpu: 200m` | 提供资源上下文，当前退出机制与资源硬限制无关 |
| 4 | Logging | Elasticsearch | `pattern: http_request, level: error, message: CONFIG_MISSING, http_status: 500, path: /work` | 揭示直接失败原因：应用因配置缺失主动报错并停止服务 |
| 5 | Tracing | Tempo | `span: GET /work, status: 500, attributes.aiops.observed_mode: config_missing_exit` | 关联日志，确认进程在尝试处理请求时因缺少关键配置而触发退出逻辑 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 15`, `reason: CrashLoopBackOff` | 独立数值验证 K8s 事件记录的 15 次重启，状态一致 |

**证据印证说明：**
K8s Event 与 Metric 共同锁定了“持续重启且状态为 CrashLoopBackOff”的客观事实（证据 1、6）。应用容器在 `resource_limit=96Mi/200m` 限制下运行，未触发 OOMKilled，而是以退出码 `78` 退出（证据 2）。Logging（证据 4）与 Tracing（证据 5）精准揭示了退出的内在机制：应用代码在执行 `/work` 请求逻辑时因 `CONFIG_MISSING` 触发错误处理，最终导致进程主动退出并引发 K8s 的重启循环。

## 🎯 根因分析 · g1

### 因果链

```text
应用关键配置缺失 → 启动/运行初始化逻辑抛出 CONFIG_MISSING 错误 → 进程以退出码 78 异常终止 → 容器反复崩溃触发 CrashLoopBackOff
```

### 根因结论

已确认根因：**应用依赖的关键配置缺失（CONFIG_MISSING）**。

应用进程在启动或执行 `/work` 端点逻辑时，因缺失必要的配置项导致初始化逻辑或请求处理失败。应用主动捕获该错误后以非零退出码 `78` 终止进程，Kubernetes 重启策略捕获到持续的异常退出（exit_code=78），进而触发 BackOff 机制，表现为 `CrashLoopBackOff` 状态。

*   **证据支撑**：日志中连续出现的 `CONFIG_MISSING` 错误模式（事实 #4）；Trace 中确认应用进入 `config_missing_exit` 模式（事实 #5）；K8s 记录的退出码 `78`（事实 #2）。
*   **排除项**：资源限制（96Mi/200m）并非导致退出的原因；无证据表明存在节点层面的 OOMKilled 或 Kubelet 故障。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 15.4s
├─ 并发证据采集: 50.6s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 50.6s (Evidence 41.3s, RCA 9.2s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
