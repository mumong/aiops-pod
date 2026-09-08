## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | Running | Pod workload-79d9f8fd88-bwqhh 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Status | `diagnostic_status: diagnosed`, `phenomenon: Pod ... 处于 CrashLoopBackOff 状态` | 确认最终异常现象为容器崩溃且系统正在反复重启。 |
| 2 | K8s Event | Prometheus | `kube_pod_container_status_last_terminated_reason` = `"Error"` (Reason: `Error`, Container: `app`) | 确认容器上一次退出的直接原因是系统触发的 Error 事件，而非普通退出。 |
| 3 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 在观察窗口内由 `25` 次激增至 `44` 次 (`trend_evaluable: true`) | 证实 Pod 正处于高频崩溃重启（BackOff）的活跃过程中。 |
| 4 | Metric | Prometheus | `kube_pod_status_phase` 中 `Failed` 状态值为 `0` (Container: `kube-state-metrics`) | 排除 Pod 本身处于 Failed 终态的情况，佐证当前主要矛盾在于容器级别的 CrashLoop。 |
| 5 | Logging | Elasticsearch | 模式：`request completed` (HTTP 200, Path: `/work`), `allocated_mib`: 连续记录中始终为 `0` | 应用成功返回 HTTP 200，表明业务逻辑本身未报错；内存分配显示为 0，与 OOM 理论上的高内存占用特征存在表面冲突，需结合 Trace 确认。 |
| 6 | Tracing | Deepflow/Tempo | Flow: `HTTP GET /work` -> 200; Span: `GET /work`, `attributes.aiops.observed_mode: liveness_fail` | 揭示关键机制：虽然应用返回了 200 且日志显示完成，但运行时健康检查（Liveness）判定失败，这是导致 CrashLoopBackOff 的典型探针机制触发。 |

**证据互证说明**：
Metric 维度（#2, #3）证实了 CrashLoopBackOff 的活跃状态与退出原因；Tracing 维度（#6）提供了机制解释，即应用层响应正常（与日志 #5 一致），但存活探针机制判定失败。日志显示的内存分配为 0 与 OOMKilled 根因存在观测冲突，但探针失败是触发重启的直接信号。

## 🎯 根因分析 · g1

### 因果链

```text
容器存活探针判定失败 (Liveness Fail) → 容器进程被健康检查机制终止 → Kubelet 重启失败容器触发 BackOff → 用户可见 Pod 状态呈现 CrashLoopBackOff
```

### 根因结论

**已确认的根因**：
Pod `workload-79d9f8fd88-bwqhh` 处于 CrashLoopBackOff 的直接触发机制是**存活探针失败 (Liveness Fail)**。
*   **证据支持**：Tracing 记录显示在 `GET /work` 请求返回 200 成功响应的同时，Span 属性明确记录了 `observed_mode: liveness_fail`（证据 #6）。
*   **结论逻辑**：尽管应用成功处理了请求并返回正常状态码（日志 #5、Tracing Flow #6），但由于存活探针未能通过检查（例如应用内部资源耗尽导致无响应或探针配置超时），导致容器进程被终止（Metric 证据 #2），进而引发 Kubelet 的频繁重启与 BackOff（Metric 证据 #3）。

**注意**：
正式 RCA 提示的 `Container OOMKilled` 与日志中连续记录的 `allocated_mib = 0` 存在事实层面的特征冲突，现有输入事实不足以确凿验证内存耗尽是根本原因，目前可审计的唯一直接终止证据为探针失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 18.0s
├─ 并发证据采集: 56.4s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 56.3s (Evidence 48.3s, RCA 7.9s)
└─ 汇总总结: 12.3s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-oomkilled
