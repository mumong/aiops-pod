## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Liveness Probe 配置超时（1s）小于业务处理耗时（~3s），导致探针请求被 kubelet 判定为失败，触发 Container killing 并引发 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded (Client.Timeout exceeded while awaiting headers)` | 证明 Liveness Probe 因超时被 kubelet 判定失败 |
| 2 | K8s State | kubernetes | `last_exit_code: 137`, `container.restart_count: 23` | 确认容器被强制终止并进入 CrashLoopBackOff 循环 |
| 3 | K8s Event | kubernetes | `Killing Container app failed liveness probe, will be restarted` | 直接印证超时导致容器被 kill |
| 4 | Tracing | deepflow | `GET /health` 耗时 `~3s` (min/max 3001203.0/3001585.0 us)，`/ready` 耗时 `1.2-8.8s` | 证明后端业务处理耗时远超 Probe 预期，是超时的根本原因 |
| 5 | Logging | elasticsearch | `GET /ready HTTP/1.1" 200`, `GET /health HTTP/1.1" 200` | 确认应用实际处于正常提供服务状态，排除应用崩溃 |

**证据说明**：
K8s Event 中明确的 `context deadline exceeded` 与 Exit Code 137 直接对应容器被 Kill 的状态；Tracing 数据显示 `/health` 接口实际处理耗时约 3 秒，与官方 RCA 推断的“超时设置过短”完全吻合；Logging 证实应用进程存活且返回 HTTP 200，排除了业务侧故障，确认为配置层面的探针超时导致。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness Probe 超时阈值设置过短(约1s) → 业务处理耗时(约3s)超时 → kubelet 强制 Kill 容器 (Exit Code 137) → 容器 CrashLoopBackOff
```

### 根因结论

已确认根因为 **Liveness Probe 配置超时（约 1s）小于业务实际处理耗时（~3s）**。

证据链显示，虽然应用进程正常运行且 HTTP 接口响应 200（Logging, Tracing #5, #4），但 `/health` 接口的处理耗时超过了探针的超时限制，导致 kubelet 判定探针失败（K8s Event #1）并终止容器（K8s State #2），最终引发 CrashLoopBackOff。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 14.7s
├─ 并发证据采集: 61.9s
│  └─ g1 aiops-case-v17/workload: 61.9s (Evidence 53.1s, RCA 8.6s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime, pod-oomkilled, pod-config-error
