## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod workload-5f4fb9ff45-5mlnc 持续 NotReady |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes Pod `aiops-case-09/workload-5f4fb9ff45-5mlnc` | Pod 状态: `Running`；重启次数: `0` | 确认 Pod 容器正在运行且未发生重启，排除 OOMKill 或应用崩溃重启场景。 |
| 2 | K8s Event | Kubernetes Pod `aiops-case-09/workload-5f4fb9ff45-5mlnc` | `Readiness probe failed: HTTP probe failed with statuscode: 503` (1974次/98m) | 确立 Readiness Probe 持续失败的客观事实，直接导致 Pod 标记为 `NotReady`。 |
| 3 | Logging | Elasticsearch (`aiops-lab-workload`) | 模式：`dependency unavailable` (HTTP 503, path: `/work`)，连续 8 次记录，时间窗口 `2026-09-11T02:10:56.848Z` 至 `02:11:24.996Z`，`allocated_mib` 始终为 `0` | 证明应用在处理 `/work` 请求时，因下游依赖不可用主动返回了 503 状态码，解释了 Probe 失败的具体原因。 |
| 4 | Tracing | Tempo / Deepflow | `GET /work` 返回 `503`，耗时约 15ms-20ms；Flow 中 `src_ip: 172.16.104.62`，`dst_ip: 172.16.104.16`；关联 Trace ID `6adec9544c6e231bb646323ac1053242` | 从网络流和链路追踪确认了 503 响应的来源和去向，证实请求已到达应用（dst_ip=Pod IP）并收到明确的 503 响应，非网络层拦截。 |

**证据关系说明：**
1. **事件与日志印证**：K8s 事件 `Readiness probe failed: ... 503`（证据 2）与日志 `dependency unavailable` 返回 `HTTP 503`（证据 3）完全对应，证明应用逻辑是故障源。
2. **链路追踪补充**：追踪数据（证据 4）显示了 `GET /work` 请求到 Pod IP `172.16.104.16` 产生了 503 响应，证实了故障发生在应用处理层而非 Pod 启动阶段。
3. **排除资源限制**：资源配置显示 CPU Limit `200m`、Memory Limit `96Mi`（上下文事实），内存监控 `allocated_mib: 0` 且重启次数为 0，排除了资源耗尽导致的 503 可能。

## 🎯 根因分析 · g1

### 因果链

```text
下游依赖服务不可用 → 应用处理 /work 请求返回 503 (dependency unavailable) → Readiness Probe 持续收到 503 响应 → Pod 状态保持 NotReady
```

### 根因结论

**已确认的根因：** Pod 应用（`aiops-lab-workload`）内部的业务逻辑依赖的下游服务不可用，导致其在处理就绪探针请求 `/work` 时返回了 `HTTP 503`。Kubernetes 检测到连续 503 响应，判定应用未就绪，从而将 Pod 状态维持在 `NotReady`。

**引用证据：**
- K8s Event 证明 Probe 失败机制（证据 2）。
- 日志证明应用返回 503 的原因是 `dependency unavailable`（证据 3）。
- Tracing 确认了 503 响应发生在应用处理链路中（证据 4）。

**未确认信息（证据不足）：**
- 导致“下游服务不可用”的根本原因是什么（如网络问题、依赖服务宕机、配置错误等）。
- 具体是哪个下游依赖组件不可用。
目前缺乏追踪跨 Pod 或跨服务的调用链数据来定位具体的上游/下游依赖关系。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 23.5s
├─ 并发证据采集: 106.0s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 106.0s (Evidence 94.3s, RCA 11.5s)
└─ 汇总总结: 19.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
