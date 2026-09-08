## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | Error | Pod workload-dff5cbc6b-kmfxx 处于 Error/CrashLoopBackOff 状态，容器 app 重启 10 次后退出，HTTP 服务不可用。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Back-off restarting failed container app` (Warning BackOff) | 确认可见故障现象为 CrashLoopBackOff |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason: Error`, `container.last_exit_code: 78` | 容器非 OOMKilled 等系统级终止，存在特定应用级异常退出逻辑 |
| 3 | K8s Event | Kubernetes | `ContainersReady: False`, `Reason: ContainersNotReady` | Pod 处于 Running 但不可用状态 |
| 4 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff`, `restart_count: 10` | 故障持续存在且已进入指数退避重启阶段 |
| 5 | Logging | Elasticsearch | 日志模式：`CONFIG_MISSING`, http_status: 500, path: `/work` (出现 8 次, 时间窗口 21:58-22:26) | 提供直接的应用级错误归因：关键配置缺失 |
| 6 | Tracing | Deepflow | L7 Flow 聚合：`HTTP GET /work`, `response_code: 500`, `response_status: 3` | 确认 HTTP 服务持续返回 500 错误，故障具有持续性 |
| 7 | Tracing | Tempo | Span：`attributes.aiops.observed_mode: config_missing_exit`, `http.response.status_code: 500` | 链路追踪确认了配置缺失导致请求处理失败并退出的机制 |

**证据关联说明：**
日志维度（#5）明确指出了故障原因是 `CONFIG_MISSING`。追踪维度（#7）提供了更细粒度的证据，显示请求在 `/work` 路径处理时触发了 `config_missing_exit` 模式。Kubernetes 维度（#2, #3）证实了这一退出模式（exitCode 78）导致了 Pod 处于 CrashLoopBackOff 状态（#1, #4）。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动或运行时无法读取关键配置 (CONFIG_MISSING) → 触发应用自定义退出逻辑 (exitCode 78, 返回 HTTP 500) → Kubernetes 容器终止并触发指数退避重启 (CrashLoopBackOff) → Pod 持续处于 ContainersNotReady 状态，服务不可用
```

### 根因结论

**已确认的根因：** 应用因缺失关键配置（日志明确显示 `CONFIG_MISSING`）而持续崩溃重启。

**证据链支撑：**
- 日志（#5）和追踪（#7）一致表明，应用在尝试处理 HTTP 请求（GET /work）时因配置缺失返回 500 并终止进程。
- Kubernetes 事实（#2）确认容器以 exitCode 78 终止，这与应用侧报告的配置缺失逻辑一致，排除了资源超配（OOMKilled）等基础设施层面的根因。
- K8s 事件（#1, #4）证实了由于上述退出机制，Pod 陷入了 `CrashLoopBackOff`。

**未知与局限：**
正式 RCA 中提到的未确认项指出，需进一步分析应用配置加载逻辑，以明确为何在挂载了 ConfigMap `workload-code` 后仍报 `CONFIG_MISSING`（例如：挂载路径映射错误、Key 拼写不匹配或 ConfigMap 内容未更新）。当前证据仅确认了“配置缺失导致崩溃”这一结果，未包含 ConfigMap 内部具体内容作为诊断证据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 17.8s
├─ 并发证据采集: 69.9s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 69.9s (Evidence 57.4s, RCA 12.3s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-config-error
