## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Container `app` state: `CrashLoopBackOff`, restart count: `16`, last exit code: `78` (Fact IDs: fact-8b8b219e969c, fact-6f2e78ce4572, fact-f52e677296de) | 确认 Pod 处于重启循环，终止原因被标记为 Error |
| 2 | K8s Event | Kubernetes | Warning `BackOff` 2m18s (x264 over 62m) for pod `workload-dff5cbc6b-sjvxl` (Fact ID: fact-bd1d8f2facf0) | 确认 Kubernetes 控制平面正在执行指数退避以抑制快速重启 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` value `1` (reason: `CrashLoopBackOff`) and `kube_pod_container_status_restarts_total` value `16` (Fact IDs: fact-2f137edd9273, fact-535292905775) | 独立数据源确认 Pod 等待状态及重启次数与 K8s 状态一致 |
| 4 | Logging | Elasticsearch | Pattern `CONFIG_MISSING` (HTTP 500 on path `/work`, trace_ids: e.g., `2e59e3c2fc52501a861c255a760760c5`), occurring 8 times between 21:02:53Z and 21:23:51Z (Fact ID: fact-0dc98f941e4c) | 提供应用进程崩溃时的具体错误上下文 |
| 5 | Tracing | Tempo/Deepflow | L7 Flow `GET /work` -> `500` with trace_ids matching logging (e.g., `2e59e3c2fc52501a861c255a760760c5`), span `aiops.observed_mode: config_missing_exit` (Fact IDs: fact-1475da77a435, fact-239265a728e1) | 跨维度关联日志 Trace ID，证明应用接收到请求后主动退出（Exit Code 78 对应 SIGUSR1/Terminated） |

**证据印证说明：**
1. K8s 状态（Fact 1, 2）证实了 Pod 反复崩溃且被系统退避；Metric（Fact 3）独立验证了该状态与重启计数。
2. 日志（Fact 4）与 Tracing（Fact 5）通过完全一致的 `trace_id` 形成闭环，证明应用内部抛出 `CONFIG_MISSING` 错误并返回 HTTP 500。
3. 应用错误码 500 及退出模式 `config_missing_exit` 解释了 K8s 观察到的 `Error` 终止原因与 Exit Code `78`。

## 🎯 根因分析 · g1

### 因果链

```text
应用请求处理逻辑遇到 CONFIG_MISSING → 应用返回 HTTP 500 并抛出 CONFIG_MISSING → 主进程以 Exit Code 78 (SIGUSR1) 终止 → K8s 检测 Error 状态并触发 CrashLoopBackOff
```

### 根因结论

已确认的根因：应用代码在请求处理期间由于配置缺失（`CONFIG_MISSING`）发生错误，主动返回 HTTP 500 并终止进程。

*   证据 4、5 明确记录了请求 `GET /work` 返回 500 并包含 `CONFIG_MISSING` 错误模式。
*   证据 1、2、3 显示该错误导致了应用进程以 `Error` 状态退出（Exit Code 78），进而引发 K8s 的 CrashLoopBackOff 机制。
*   应用日志中记录的 `aiops.observed_mode: config_missing_exit` 直接印证了这是由特定配置缺失导致的预期内崩溃行为。

缺失的决定性事实：具体缺失的配置键或文件名称，以及配置未能注入 Pod 的原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 24.0s
├─ 并发证据采集: 50.7s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 50.7s (Evidence 41.1s, RCA 9.5s)
└─ 汇总总结: 14.1s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime, pod-oomkilled
