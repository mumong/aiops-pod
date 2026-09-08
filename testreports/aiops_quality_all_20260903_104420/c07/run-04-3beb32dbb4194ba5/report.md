## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-kmfxx 处于 CrashLoopBackOff 状态，容器 app 连续重启 5 次，退出码 78。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `status: CrashLoopBackOff`, `restart_count: 5`, `exit_code: 78` | 确认应用进程持续以退出码 78 终止并重启的症状。 |
| 2 | K8s State | Kubernetes | `Waiting Reason: CrashLoopBackOff`, `message: back-off 2m40s restarting failed container=app` | 确认当前 Pod 处于等待重启阶段，而非正常运行。 |
| 3 | K8s Event | Kubernetes | `Warning BackOff ... Back-off restarting failed container app ...` | 提供 `kubelet` 记录的具体重启退避行为。 |
| 4 | Logging | Elasticsearch | `pattern: {event: http_request, level: error, message: CONFIG_MISSING, http_status: 500, path: /work}`, `occurrence_count: 8`, `time_range: 13:59:02 - 14:02:44` | 证明崩溃前应用多次收到 HTTP 500 请求，且错误原因为配置缺失。 |
| 5 | Tracing | Deepflow | `GET /work`, `response_code: 500`, `response_status: 3`, `src_ip: 172.16.104.9 -> dst_ip: 172.16.104.15` | 提供 L7 层面的失败证据，确认 Pod IP 172.16.104.15 持续返回 500 错误。 |
| 6 | Tracing | Tempo | `http.route: /work`, `http.response.status_code: 500`, `aiops.observed_mode: config_missing_exit` | 关联具体 Trace ID 确认是应用内部逻辑因配置问题主动退出。 |
| 7 | Metric | Prometheus | `kube_pod_container_status_waiting_reason {reason: "CrashLoopBackOff"}: 1`, `kube_pod_container_status_restarts_total: 5` | 从监控视角独立验证了 Pod 等待状态及重启总数，与 K8s State 一致。 |
| 8 | Metric | Prometheus | `container_memory_working_set_bytes (container: app): 3420160` bytes | 确认重启前内存未突破 Limit (96Mi)，排除 OOMKill 导致 crash。 |

**证据说明：**
*   **现象确认**：K8s State (事实 1, 3) 与 Metric (事实 7) 共同印证了 Pod 处于 CrashLoopBackOff 状态且已重启 5 次。
*   **根因定位**：Logging (事实 4) 中反复出现的 `CONFIG_MISSING` 错误与 Trace (事实 6) 中明确的 `config_missing_exit` 模式高度吻合，证实了进程退出的直接原因是业务层面的配置加载失败。
*   **排除干扰**：Metric (事实 8) 显示内存使用量远低于 Limit，结合退出码 78（通常用于应用自定义退出），排除了 OOM 或系统资源限制导致的异常退出。
*   **网络关联**：Deepflow Flow (事实 5) 将失败的 HTTP 流量精确指向了该 Pod 的 IP，证实了上述错误日志与网络请求的时间与空间关联。

## 🎯 根因分析 · g1

### 因果链

```text
关键配置缺失 (CONFIG_MISSING) → 应用业务逻辑抛出异常并返回 HTTP 500 → 进程以自定义退出码 78 终止 → kubelet 检测到退出并触发 CrashLoopBackOff 重启
```

### 根因结论

**已确认的根因：** 应用启动后在处理请求时检测到关键配置缺失（日志报 `CONFIG_MISSING`），导致程序主动抛出异常并以退出码 78 终止，进而引发 K8s 的 `CrashLoopBackOff` 重启机制。

**证据支持：**
*   **日志与追踪印证**：日志记录了 8 次 `CONFIG_MISSING` 错误（事实 4），追踪记录了多次 `config_missing_exit` 模式（事实 6），两者均指向同一个应用逻辑缺陷或环境配置问题。
*   **退出码吻合**：K8s 记录的 `exit_code: 78`（事实 1）与追踪中的 `config_missing_exit` 模式一致，排除了资源耗尽或容器运行时故障。

**未知项（需补充调试）：**
*   具体缺失的配置字段名称（日志仅打印 `CONFIG_MISSING`，未包含变量名）。
*   配置未加载的原因（缺乏 Pod 定义中环境变量或 ConfigMap/Secret 挂载的直接证据，需进一步检查 Pod 的 `yaml` 配置以确认引用关系）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 13.3s
├─ 并发证据采集: 84.1s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 84.1s (Evidence 69.7s, RCA 14.2s)
└─ 汇总总结: 15.9s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
