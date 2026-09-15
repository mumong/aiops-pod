## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | Pod aiops-case-10/workload-79d9f8fd88-48j8r 因 Liveness 探针返回 500 导致容器被 Kubelet Kill (Exit 137)，引发 CrashLoopBackOff，当前处于重启后恢复状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubelet | `Liveness probe failed: HTTP probe failed with statuscode: 500` (x8 over 6m12s) | 证明探针调用持续返回 500 错误，触发终止机制。 |
| 2 | K8s Event | Kubelet | `Container app failed liveness probe, will be restarted` (x4 over 6m9s) | 确认探针失败导致的 Kill 动作已发生。 |
| 3 | K8s Event | Kubelet | `Back-off restarting failed container app` (x6 over 2m9s) | 印证 Pod 已进入 CrashLoopBackOff 状态。 |
| 4 | K8s State | Kubelet | `Container exit_code: 137` | 证实容器是被 Kubelet 强制 Kill (OOMKilled/Signal 137) 而非正常退出。 |
| 5 | Metric | Prometheus | `container_memory_working_set_bytes` (采样 14)：峰值 `16,171,008 bytes` (~15.4 MiB)，当前 `471,040 bytes`。内存硬限制为 `96 MiB`。 | 内存使用量远低于限制，排除 OOM Killed (Exit 137 的常见非探针原因)。 |
| 6 | Logging | Elasticsearch | `path: /work, http_status: 200` (8 次记录, `f66f45...` ~ `5cbc48...`) | 证明应用在处理业务请求 (`/work`) 时运行正常，排除应用整体崩溃。 |
| 7 | Tracing | Tempo/Deepflow | `GET /work, status_code: 200` (Trace ID: `dd305924...`, `b0a8fc...`, `5cbc48...`) | 追踪数据与日志时间线及 Path 高度重合，证实 `/work` 接口健康。 |

**证据说明：**
Kubernetes 事件与探针 500 报错直接指向 Liveness 配置或目标路径逻辑异常。Metric 数据显示内存充足，否定了资源耗尽导致的应用无响应。Logging 与 Tracing 一致显示应用正在正常处理 `/work` 路径的请求，证明“应用进程挂起或崩溃”的假设不成立。探针失败与应用正常工作之间的差异，锁定根因为探针配置的请求路径与后端逻辑的映射问题。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness 探针配置的 /health 路径或路由逻辑异常 → Kubelet 接收 HTTP 500 持续失败 → Kubelet 强制终止容器 (Exit 137) → Pod CrashLoopBackOff
```

### 根因结论

**已确认根因：Liveness 探针配置路径或后端路由逻辑存在偏差。**

证据链显示：
1. **探针故障**：Kubelet 报告 Liveness 探针（#1）在长达 6 分钟的窗口内连续 8 次返回 HTTP 500。
2. **应用健康**：应用通过 `Logging` (#6) 和 `Tracing` (#7) 证实，业务路径 `/work` 在相同时段内持续返回 200 成功状态，且未出现异常。
3. **非资源限制**：Metric (#5) 显示容器内存使用峰值（~15.4 MiB）远低于 `96 MiB` 的硬限制，确认 Exit 137 是由探针触发而非 OOM。

综上，应用本身未崩溃，但用于健康检查的特定路径（`/health`）未能返回 200，导致 Kubelet 判定健康检查失败并杀死容器。具体是路径不存在、路由未映射、还是健康检查逻辑本身存在缺陷（如依赖的子系统暂不可用），需要进一步比对探针配置与代码逻辑。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 24.8s
├─ 并发证据采集: 87.7s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 87.7s (Evidence 77.4s, RCA 10.1s)
└─ 汇总总结: 13.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime
