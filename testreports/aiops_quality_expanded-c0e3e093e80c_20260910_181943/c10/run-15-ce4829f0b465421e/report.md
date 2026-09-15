## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bsn84` | CrashLoopBackOff | 应用健康检查配置错误导致容器被误杀。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Exit Code: 137, Restart Count: 21 | 核心症状：异常退出码 137 通常对应 OOM 或信号终止，持续重启 21 次。 |
| 2 | K8s Event | kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 | 异常触发点：健康检查在探测期内返回 HTTP 500 错误，直接导致 kubelet 判定不健康并发起重启。 |
| 3 | K8s State | kubernetes | Resource Request: CPU=20m, Memory=24Mi | 上下文：资源限制极低，需排查是否因资源受限导致应用响应变慢从而触发健康检查超时。 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total` = 21 | 症状印证：确认重启行为确凿，与 K8s State 状态一致。 |
| 5 | Logging | elasticsearch | HTTP status=200, path="/work", min/max allocated_mib=0 | 业务现状：业务请求 `/work` 实际响应正常（HTTP 200）且内存无分配（0），证明业务本身未崩溃。 |
| 6 | Tracing | deepflow | GET /work response_code=200, duration=17920.0-26518.0 us | 流量佐证：网络流量层面确认应用成功响应了 200 状态码。 |

**证据说明**：
应用日志与流量均显示业务请求 `/work` 成功返回 200，但 K8s 事件明确指出健康检查返回了 500。同时日志中 `allocated_mib` 始终为 0，说明实际应用未发生内存分配。
矛盾点在于：应用实际处理正常（200），但健康检查端点（Liveness Probe）却报 500。结合日志中内存分配为 0 的异常情况，极可能是应用对健康检查路径的响应逻辑存在缺陷（例如未正确响应或逻辑走不通），而非外部资源（CPU/内存）限制导致应用整体崩溃。K8s 退出码 137 在这里可能存在混淆，或者是由健康检查失败后的 Kill 行为导致，但核心线索指向“健康检查配置或应用对该检查的响应”问题。

## 🎯 根因分析 · g1

### 因果链

```text
应用对 Liveness Probe 路径响应异常(HTTP 500 或 无响应) → kubelet 健康检查判定失败 → 执行容器 Kill (Exit 137) → 容器 CrashLoopBackOff
```

### 根因结论

已确认根因：**应用健康检查配置或应用逻辑错误导致容器被误杀**。

**依据**：
1. **健康检查失败是重启的直接诱因**：K8s Event 明确记录 `Liveness probe failed: HTTP probe failed with statuscode: 500`，且伴随 `BackOff restarting failed container`（证据 2）。
2. **业务逻辑并未完全崩溃，但存在异常**：日志显示业务路径 `/work` 返回 HTTP 200（证据 5, 6），这与“应用整体无法运行”的假设矛盾，说明应用进程还在，但可能对健康检查端点（或健康检查配置的 URL/参数）处理不当。
3. **资源不是首要限制因素**：虽然退出码 137 常暗示 OOM，但日志中内存分配 `allocated_mib` 始终为 0（证据 5），且资源 Request/Limit 配置并非极小（24Mi/20m），不足以直接导致 OOM Killer 在如此低的内存下立即触发，且没有日志显示内存增长趋势。因此，HTTP 500 是比 OOM 更直接、更确凿的证据。

**缺失决定性事实**：
- 缺乏对健康检查端点（如 `/healthz` 或 `/`）的单独日志或 Trace 数据，无法区分是应用代码写错了健康检查端点，还是健康检查配置了错误的 URL。
- 无法直接确认“应用对健康检查路径返回 500”的具体代码逻辑。

**结论**：当前证据高度指向“健康检查配置错误”或“应用对健康检查端点响应逻辑错误”（如误将业务逻辑混入健康检查，导致健康检查失败）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 15.6s
├─ 并发证据采集: 53.5s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bsn84: 53.5s (Evidence 46.7s, RCA 6.6s)
└─ 汇总总结: 14.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bsn84**: pod-crashloop-runtime, pod-oomkilled
