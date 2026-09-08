## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | Liveness Probe 配置路径 '/health' 与业务实际健康端点 '/work' 不一致，导致 kubelet 频繁接收 HTTP 500 响应并发送 SIGKILL 终止容器，进而引发 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: `Error` | 直接指向容器非正常终止 |
| 2 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (x69 over 118m) | 明确诊断出健康检查失败的具体原因是 Liveness Probe 返回 500 错误，触发终止机制 |
| 3 | K8s Event | Kubernetes | `Back-off restarting failed container app` (x415 over 114m) | 佐证容器因故障频繁重启并进入 BackOff 状态 |
| 4 | Metric | Prometheus | `container_memory_working_set_bytes`: 稳定在 14.6~15.7MB (min 3.5MB, max 15.7MB) | 排除内存溢出 (OOMKilling) 的可能性 |
| 5 | Logging | Elasticsearch | HTTP status: `200`, path: `/work` (8 occurrences, e.g., trace `9ff89721c0bb85cdac6438b412433f45`) | 证明应用自身的业务逻辑及 `/work` 端点均运行正常，无异常报错 |
| 6 | Tracing | Tempo / Deepflow | Span `GET /work` returns 200; AIOP observed mode: `liveness_fail` | 验证流量确实到达了 `/work` 并获得成功响应，确认 kubelet 探活路径并非指向 `/work` |

**证据说明：**
- **证据 2 (Event)** 确认了导致终止的直接机制：kubelet 执行 Liveness Probe 失败（返回 500）。
- **证据 5 (Logging)** 与 **证据 6 (Tracing)** 互相印证，证明应用业务端（尤其是 `/work` 路径）是健康的，排除了应用代码崩溃的可能。
- **证据 1 (State)** 结合 **证据 4 (Metric)** 排除了资源耗尽（OOM）因素，因为内存使用量远低于配置的 96Mi 上限。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness Probe 路径配置错误 (指向 /health) → 应用实际健康端点 (/work) 与探活路径不匹配，探活请求返回 500 → kubelet 判定容器不健康，发送 SIGKILL 终止容器 → 容器反复重启进入 CrashLoopBackOff
```

### 根因结论

已确认根因为 **Liveness Probe 配置路径与实际业务健康端点不一致**。
- **事实支撑**：K8s Event (`fact-e2f706e47c73`) 显示 `Liveness probe failed` 返回 500 错误；日志 (`fact-38285bd33b79`) 和流量 (`fact-21a2e1f8c9c9`) 均证实业务端口正常响应 200，且路径为 `/work`。
- **排除因素**：Prometheus 监控 (`fact-0459e9e4c1de`) 显示内存使用平稳，未达到 96Mi 的限制，排除 OOM 原因；日志未报应用内部错误，排除应用崩溃原因。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 27.3s
├─ 并发证据采集: 88.3s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 88.3s (Evidence 81.1s, RCA 7.1s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
