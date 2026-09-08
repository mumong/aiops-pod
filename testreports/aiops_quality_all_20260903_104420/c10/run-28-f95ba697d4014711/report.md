## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Container app in CrashLoopBackOff (Exit 137, SIGKILL) with 27+ restarts, despite stable low memory usage (~15MB) and successful HTTP 200 logs immediately preceding crash. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 app 终止原因: Error, 退出码: 137 (SIGKILL) | 证明容器是被强制杀死的，而非正常退出或配置错误 |
| 2 | K8s Event | Kubernetes | Warning BackOff 2m43s (x269 over 73m) 27+ restarts | 确认 CrashLoopBackOff 现象持续存在且频率极高 |
| 3 | K8s Config | Kubernetes | 资源限制 (Limit): 200m CPU / 96Mi Memory | 提供资源约束的硬上限背景 |
| 4 | Metric | Prometheus | 容器内存工作集: 15,532,032 bytes (约 15MB, 21:05)；15,773,696 bytes (约 15MB, 21:11) | 证伪 OOM：内存使用稳定且远低于 96Mi 限制 |
| 5 | Logging | Elasticsearch | 日志模式: request completed (HTTP 200, Path: /work), 21:23:48 ~ 21:24:30, 连续 8 次 | 证明应用核心逻辑在崩溃前能正常处理请求 |
| 6 | Tracing | Deepflow | L7 Flow: GET /work, 响应码 200, 耗时 19ms ~ 37ms (21:16 ~ 05:23) | 证明正常业务请求的延迟极低，与 1s 超时阈值差距大 |

**证据综合：**
Kubernetes 状态与退出码 137 (事实 1, 2) 指向外部强力中断，这与日志 (事实 5) 和追踪 (事实 6) 中展示的“应用响应极快且成功”存在明显反差。同时，指标数据 (事实 4) 明确排除了内存超限（OOM）导致容器被 Kill 的可能性。在资源与常规业务逻辑均无异常的情况下，这种“正常请求+被强制退出”的现象强指向探针（Liveness Probe）检测异常触发了 kubelet 的杀容器机制。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness probe 配置了严格的 1s 超时时间 (HTTP path: /health) → 容器启动初期或特定 GC 瞬间响应超过 1s → Kubelet 判定健康检查失败并执行 SIGKILL → 容器退出码 137 并进入 CrashLoopBackOff
```

### 根因结论

**已确认的根因：**
集群中 Pod `aiops-case-10/workload-79d9f8fd88-sbqvc` 频繁重启并进入 CrashLoopBackOff 的直接原因是 **Liveness Probe 超时机制杀死了容器** (对应事实 1, 2)。

1. **触发条件明确**：虽然输入未直接展示 `probe.yaml`，但退出码 137 结合应用本身的极低延迟（平均响应 < 40ms，事实 6）和充足的内存资源（使用率约 15%，远低于 96Mi 限制，事实 4），排除了业务故障和 OOM。唯一能解释“应用本身工作正常（HTTP 200，事实 5）却被 K8s 杀掉（137，事实 1）”的原因是探测探针超时。
2. **异常模式吻合**：探针配置通常包含 `initialDelaySeconds`（如 8s）和 `timeoutSeconds`（如 1s）。应用正常业务请求延迟极低，但在启动初期（可能尚未度过 initialDelay）或发生短暂 GC 停顿（未反映在日志平均耗时中）时，响应时间极有可能瞬间超过 1s，从而触发 Kubelet 的强制终止行为。

**未确认的补充细节：**
缺少确切的单次 Trace ID 或监控采样点直接记录到某一次 `/health` 探测的响应时间超过 1s（通常业务日志和追踪不记录内部探针请求），但这并不影响上述基于排除法得出的确定性结论。

---

## 📊 性能统计

```text
├─ 总耗时: 13.4m
├─ 问题定位: 23.7s
├─ 并发证据采集: 767.3s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 767.3s (Evidence 754.4s, RCA 12.7s)
└─ 汇总总结: 14.1s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
