## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | Running | Pod aiops-case-10/workload-79d9f8fd88-bwqhh 处于 CrashLoopBackOff 状态（Ready=False），容器退出码 137。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` | 确证 Liveness 探针探测失败的具体原因 |
| 2 | K8s State | Kubernetes | `Exit Code: 137` | 确证容器进程被终止，直接对应 K8s Event 的 CrashLoop 现象 |
| 3 | K8s State | Kubernetes | `pod.status: Running` | 提供 Pod 当前处于存活但容器不健康的上下文 |
| 4 | K8s Config | Kubernetes | `resource_limit.memory: 96Mi` | 提供内存限制配置，用于评估内存相关故障可能性 |
| 5 | Metric | Prometheus | `container_memory_working_set_bytes: 15421440` (约 14.7 MiB, timestamp: 2026-09-07T22:18:25Z) | 采样点表明 Pod 实际内存使用远低于 96Mi 限制，排除 OOMKilled 为直接原因 |
| 6 | Logging | Elasticsearch | `request completed` (path: `/work`, http_status: 200, min/max allocated_mib: 0) | 展示应用常规请求成功，但日志未包含 `/health` 端点的请求记录，未提供反向证据 |
| 7 | Tracing | Deepflow/Tempo | `GET /work` (response_code: 200, src_ip: 172.16.104.39 -> dst_ip: 172.16.104.32) | 提供流量链路，确认正常业务流量可达，与 `/health` 失败形成现象对比 |

证据 1 和 2 共同构成了 Pod 崩溃的直接机制：探针失败导致 kubelet 终止容器，而退出码 137 证实了系统层面的强制终止。证据 5 结合 K8s 内存配置说明，当前内存使用量极低，因此退出码 137 并非由 OOM 引起，支持了 Liveness 探针失败是主因的推论。

## 🎯 根因分析 · g1

### 因果链

```text
应用 /health 端点返回 HTTP 500 → kubelet Liveness Probe 连续失败 → 容器进程被强制终止 (Exit Code 137) → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因是应用 `/health` 端点返回 HTTP 500 导致 Liveness Probe 失败（证据编号 1），进而触发 kubelet 终止容器（证据编号 2）。内存指标（证据编号 5）远低于 Limit，排除了 OOM 的可能性。虽然日志（证据编号 6）和链路数据（证据编号 7）未能捕获 `/health` 请求本身以确认其内部逻辑错误，但现有证据已足以判定外部表现层的根因为 Liveness 探测机制触发。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 19.6s
├─ 并发证据采集: 67.1s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 67.1s (Evidence 56.6s, RCA 10.3s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-oomkilled
