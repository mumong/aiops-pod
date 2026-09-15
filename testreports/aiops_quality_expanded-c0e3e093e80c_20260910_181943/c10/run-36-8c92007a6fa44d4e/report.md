## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | Pod aiops-case-10/workload-79d9f8fd88-48j8r 处于 CrashLoopBackOff 状态，表现为 Liveness Probe 失败（HTTP 500）及容器异常重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.status`: Running, `restart_count`: 16, `last_exit_code`: 137 | 展示容器频繁重启且退出码为 137 的症状 |
| 2 | K8s Event | Kubernetes | `Unhealthy`: Liveness probe failed: HTTP probe failed with statuscode: 500 (x30 over 41m) | 证明触发重启的直接原因：Liveness Probe 连续失败 |
| 3 | K8s Event | Kubernetes | `Killing`: Container app failed liveness probe, will be restarted | 确认 kubelet 在 Probe 失败后执行了 Kill 动作 |
| 4 | Logging | Elasticsearch | `GET /work` 请求完成且返回 HTTP 200 (8次), `allocated_mib` min/max 均为 0 | 确认应用服务本身未完全挂死，且无内存使用记录 |
| 5 | Tracing | Tempo | Trace ID `d5a62cb858563f8601fccacaacc99129`, Span `GET /work`, Status Code: 200 | 关联确认应用逻辑中 `/work` 路径能成功返回 |
| 6 | Tracing | Deepflow | HTTP Flow GET /work, src_ip 172.16.104.33 -> dst_ip 172.16.104.34, 响应码 200 | 进一步验证网络层应用健康 |
| 7 | Metric | Prometheus | `kube_pod_container_status_waiting_reason`: CrashLoopBackOff (1), `restarts_total`: 15 | 从观测侧佐证了 Pod 处于重启等待状态 |

**证据说明：**
1.  **因果链条印证**：K8s Event (编号2, 3) 明确指出了 `Liveness probe failed` 是触发 `Killing` 的原因，直接解释了为何 Exit Code 为 137 (编号1)。
2.  **异常限定**：尽管 Logging (编号4) 和 Tracing (编号5, 6) 显示 `/work` 路径能返回 HTTP 200 且未发生内存激增，但 Liveness Probe 仍然返回 500 (编号2)。这证实了异常并非应用完全崩溃，而是特定健康检查端点（推测为 `/health`，因 `/work` 正常）的间歇性故障或阻塞。
3.  **资源上下文**：内存配置上限为 96Mi (Context)，但 Log 显示 allocated_mib 为 0，结合 Tracing 数据，暂无确凿证据指向 OOM，Exit Code 137 更大概率是 Kubelet 强杀的结果而非 OOM Kill 本身。

## 🎯 根因分析 · g1

### 因果链

```text
应用业务逻辑异常（推测为 /health 端点） → Liveness Probe 返回 500 失败 → Kubernetes 强制杀死容器 (Kill) → Pod 进入 CrashLoopBackOff
```

### 根因结论

**已确认的根因机制**：
Pod `aiops-case-10/workload-79d9f8fd88-48j8r` 的 `CrashLoopBackOff` 状态是由 **Liveness Probe 失败导致的容器终止** 引起的。Kubernetes 观测到健康检查 HTTP 请求返回 `500` 错误（证据 #2），随后执行 Kill 操作导致容器以 `137` 退出码重启（证据 #1, #3）。

**待确认的盲区**：
尽管应用能正常处理 `/work` 业务请求（证据 #4, #5, #6），但触发 Probe 失败的端点（通常非业务路径）的代码级原因（如死锁、超时或特定状态下的异常）在日志和追踪中未显现（日志中仅观察到正常的 200 请求）。此外，Exit Code 137 究竟是因 Probe 失败触发正常 Kill，还是同时伴随 OOM 触发，当前证据不足以做最终区分，但明确排除了应用完全崩溃或不可用的情况。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 15.5s
├─ 并发证据采集: 69.9s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 69.9s (Evidence 56.0s, RCA 13.6s)
└─ 汇总总结: 13.9s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime, pod-oomkilled, pod-config-error
