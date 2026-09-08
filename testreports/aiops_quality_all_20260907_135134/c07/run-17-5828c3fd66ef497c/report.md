## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Application startup logic fails because it cannot find the expected configuration key/file (CONFIG_MISSING) at path '/work'. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase=Running`, `pod.status=Running` | 确认 Pod 已调度并处于运行阶段 |
| 2 | K8s State | Kubernetes | `container.waiting_reason=CrashLoopBackOff`, `container.waiting_message=back-off 5m0s restarting` | 明确应用容器因崩溃陷入指数退避重启循环 |
| 3 | K8s State | Kubernetes | `container.last_terminated_reason=Error`, `container.last_exit_code=78` | 证实应用进程异常退出，且返回码为 78 |
| 4 | K8s Event | Kubernetes | `Warning BackOff: Back-off restarting failed container app` | 记录 kubelet 在 29 分钟内 131 次重启尝试 |
| 5 | Logging | Elasticsearch | `CONFIG_MISSING` at path `/work`, http_status=500 (8 次聚合) | 直接捕获应用业务逻辑错误，指向配置缺失 |
| 6 | Tracing | Tempo/Deepflow | `GET /work` 500, `aiops.observed_mode=config_missing_exit`, trace_ids 与日志一致 | 将外部请求失败与内部配置缺失模式在时间线上关联 |
| 7 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason(Error)=1`, `restarts_total` 从 5 增至 10 | 从监控指标侧印证应用反复以 Error 状态退出 |
| 8 | Metric | Prometheus | `kube_pod_container_status_waiting_reason(CrashLoopBackOff)=1` | 确认 Pod 在监控窗口内持续处于等待重启状态 |

**证据关联分析**：
Kubernetes 状态显示容器在 CrashLoopBackOff 中反复重启，Metric 佐证了重启频率的持续增加。Logging 和 Tracing 共同指出每次启动时的具体失败点：应用访问 `/work` 时因 `CONFIG_MISSING` 返回 500 并退出（Exit Code 78）。Tracing 中的 `aiops.observed_mode` 与日志的 `CONFIG_MISSING` 相互印证，明确了故障的具体业务原因。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动逻辑中未找到预期配置 (CONFIG_MISSING) → App 返回 Exit Code 78 异常终止 → Kubelet 触发重启策略并进入指数退避 → Pod 持续处于 CrashLoopBackOff 状态
```

### 根因结论

**已确认的根因**：
Pod `aiops-case-07/workload-dff5cbc6b-fkzvn` 中的应用容器因启动逻辑失败而陷入 CrashLoopBackOff。具体而言，应用在访问路径 `/work` 时触发 `CONFIG_MISSING` 错误，随后以退出码 78 终止自身。

*   **证据支撑**：
    *   **业务层失败**：Logging 显示 8 次 `CONFIG_MISSING` 错误，Tracing 确认了相同的 `config_missing_exit` 模式（见证据 5, 6）。
    *   **容器行为**：Kubernetes 状态记录容器以 `Error` 终止，退出码为 `78`（见证据 3）。
    *   **集群影响**：Metric 和 Event 记录了由此导致的 `CrashLoopBackOff` 和持续上升的重启计数（见证据 4, 7, 8）。

**未确认项**：
正式 RCA 指出尚不确定 `workload-code` ConfigMap 中具体缺失的是哪个配置键/文件，以及为何应用选择使用退出码 78 而非标准错误码。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 17.4s
├─ 并发证据采集: 96.1s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 96.1s (Evidence 84.7s, RCA 11.3s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime, pod-oomkilled, pod-config-error
