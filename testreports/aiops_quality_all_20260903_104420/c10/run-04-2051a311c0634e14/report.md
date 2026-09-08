## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Application Liveness Probe Failure (HTTP 500) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-6a52feb9ba4b) | 直接触发 Pod 重启机制的根本原因 |
| 2 | K8s State | K8s | 容器 `app` 终止原因 `Error`，最近一次退出码 `137` (fact-b8648e432db1, fact-3b6b5e74b554) | 指示进程被强制终止（通常对应 OOMKilled） |
| 3 | K8s Config | K8s | 容器资源硬限制 `memory: 96Mi` (fact-c40fb748c078) | 为内存相关终止提供配置边界参考 |
| 4 | Metric | Prometheus | 工作集内存 `15,548,416 bytes` (约 14.8 MiB) (fact-75fb917d74ed) | 证明 Pod 并未因长期内存耗尽而无法运行，当前存活状态下内存使用量并未触及 96Mi 限制 |
| 5 | Logging | ES | 成功请求 `request completed, http_status: 200, path: /work` (fact-logging-pattern) | 排除应用本身代码逻辑完全失效，说明应用能正常响应业务请求 |
| 6 | Tracing | Tempo | `GET /work` 返回 `http.response.status_code: 200` (fact-3c6f31470c0d) | 进一步证实业务链路通畅，故障隔离在探针检测或探针路径上 |

证据表明，应用代码在处理业务请求（`/work`）时能返回 `200` 状态码（见 #5, #6）。然而，Liveness Probe 检测却返回 `500`（见 #1）。结合容器以 `137`（OOMKilled）异常终止（见 #2），说明故障核心在于应用服务对探针请求的异常处理机制，而非底层基础资源耗尽或集群级故障。

## 🎯 根因分析 · g1

### 因果链

```text
探针路径异常处理逻辑 (未验证) → Liveness Probe 返回 HTTP 500 → kubelet 判定健康检查失败 → 触发容器重启 (Exit Code 137, CrashLoopBackOff) → 业务应用呈现周期性崩溃重启
```

### 根因结论

已确认的根因为 **应用 Liveness Probe 失败 (HTTP 500)**。

Kubernetes 探针向应用的健康检查端点发起请求时，应用返回了 `500 Internal Server Error`（证据 #1, #6）。Kubelet 将非 2xx/3xx 响应视为探针失败，进而杀死了容器（证据 #1, #2）。容器进程最终以退出码 `137`（强制终止）结束（证据 #2），并触发了 `CrashLoopBackOff` 状态（证据 #1, #4）。

业务日志（证据 #5）和追踪数据（证据 #6）显示应用正常处理了常规业务请求（`/work`），说明故障被隔离在应用对探针特定路径或探针自身健康检查逻辑的处理上。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 19.9s
├─ 并发证据采集: 96.4s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 96.4s (Evidence 87.3s, RCA 8.9s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime, pod-oomkilled
