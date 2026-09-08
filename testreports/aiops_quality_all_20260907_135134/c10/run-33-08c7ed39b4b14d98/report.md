## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | Pod workload-79d9f8fd88-bwqhh 处于 CrashLoopBackOff 状态，容器 app 以 exitCode 137 被终止 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff`, `container.last_terminated_reason: Error`, `container.last_exit_code: 137` (fact-07a69b1f9eac, fact-f26b840dfd22, fact-2ce6aeae53a9) | 确认容器处于 CrashLoopBackOff 循环，且最后终止码 137 表明是被强制终止 (SIGKILL)。 |
| 2 | K8s Event | Kubernetes | `Unhealthy` (x43 over 87m): `Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-9a0b1c6146c2) | 确认 Liveness Probe 返回 500 是引发容器重启的直接触发机制。 |
| 3 | Metric | Prometheus | `container_memory_working_set_bytes`: 22:04 (3649536 B), 22:17 (3354624 B) (fact-65b4c79561b1, fact-21edddd6c230) | 容器内存使用量 (~3.2-3.6 MB) 远低于 memory limit (96Mi)，排除 OOMKilled 原因。 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory: 96Mi`, `container.resource_request.memory: 24Mi` (fact-1b49320ac9d9, fact-07a69b1f9eac) | 确认内存资源限制阈值，辅助确认非资源耗尽导致的终止。 |
| 5 | Logging | Elasticsearch | Pattern `request completed`: `http_status: 200`, `path: /work`, time_range 22:17:47 - 22:18:17 (fact-2be4c14b93ba) | 应用日志显示正常路径 /work 返回 200，且时间窗口与 CrashLoop 重叠，表明正常业务并未崩溃。 |
| 6 | Tracing | Deepflow/Tempo | Flow/Flow: `GET /work`, `response_code: 200` (fact-34dfe70d27a8); Trace: `aiops.observed_mode: liveness_fail`, `http.response.status_code: 200` (fact-5c8fe5cc8208) | Tracing 显示业务路径返回 200，与 K8s Event 的 500 矛盾，提示可能 Probe 路径与业务路径不同，或存在瞬时异常。 |
| 7 | K8s Event | Kubernetes | `BackOff` (x303 over 83m): `Back-off restarting failed container app` (fact-13325bb70900) | 记录容器重启频率随时间增加，符合 CrashLoopBackOff 的指数退避特征。 |

**证据分析**：
Kubernetes 事件与状态事实（证据 1、2）确凿表明 `exitCode 137` 是由 Liveness Probe 返回 `HTTP 500` 引发的。Metrics 数据（证据 3、4）排除了内存耗尽（OOM）作为终止原因。Logging（证据 5）与 Tracing（证据 6）显示业务请求 `/work` 正常返回 200，这与 Probe 返回的 500 形成事实冲突，证实应用服务本身未发生全局宕机，而是 Probe 探测到的特定路径或特定时刻出现了异常。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness Probe 返回 HTTP 500 (服务异常) → kubelet 执行 kill (SIGKILL) 触发 exitCode 137 → 容器重启失败进入 CrashLoopBackOff → Pod 处于 CrashLoopBackOff 状态且应用不可用
```

### 根因结论

- **已确认的根因**：Pod `workload-79d9f8fd88-bwqhh` 处于 CrashLoopBackOff 状态的直接原因是 Liveness Probe 失败。Kubernetes 事件明确记录了 Liveness Probe 返回 `HTTP 500`，导致 `kubelet` 杀死容器（终止码 137），进而触发重启循环（证据 1、2）。由于内存使用量极低，该重启并非由资源不足引起（证据 3、4）。
- **未确认项**：尽管应用日志和 Tracing 记录显示业务路径 `/work` 正常返回 200（证据 5、6），但与 Liveness Probe 的 500 响应存在不一致。根本原因可能是 Liveness Probe 配置的业务路径与日志记录的业务路径不同，或者 Probe 失败是由短暂的依赖超时/拥塞引起，当前证据不足以完全解析这一表观冲突。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 21.8s
├─ 并发证据采集: 95.1s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 95.1s (Evidence 82.6s, RCA 12.2s)
└─ 汇总总结: 16.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
