## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | 应用容器依赖的配置资源缺失导致启动失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container: app, reason: CrashLoopBackOff (fact-4a81fe78b67a) | 确认异常实体状态 |
| 2 | K8s Event | kubernetes | Back-off restarting failed container app in pod workload-dff5cbc6b-kmfxx (fact-3c8bdfbaa6f2) | 记录容器启动失败的持续重试现象 |
| 3 | K8s State | kubernetes | container: app, exit_code: 78 (fact-1e1cb92a5992) | 记录应用进程的异常退出码 |
| 4 | Metric | prometheus | kube_pod_container_status_restarts_total: 11 (fact-a544f7fa05ad) | 证实容器经历了多次重启 |
| 5 | Metric | prometheus | reason: CrashLoopBackOff (fact-2ea714249674) | 从监控维度印证容器状态 |
| 6 | Logging | elasticsearch | pattern: CONFIG_MISSING, http_status: 500, path: /work (fact-604d69142d48等, 出现8次, trace_ids包括afd42312等) | 明确指向应用层配置资源缺失的错误 |
| 7 | Tracing | deepflow+tempo | flow: GET /work → 500 (fact-03150229f37a等, 9次) / span: aiops.observed_mode: config_missing_exit (fact-5888072297e4) | 流量层与应用链路层共同确认 500 错误及故障模式 |

**证据综合：** K8s 原生状态与监控数据一致证实容器处于 `CrashLoopBackOff` 且重启了 11 次。日志明确报告 `CONFIG_MISSING`，Tracing 数据（Flow 与 Span）不仅确认了对外请求返回 500 的状态码，更通过 `aiops.observed_mode: config_missing_exit` 标记直接锁定了“配置缺失”这一内部执行路径，三者形成因果闭环。

## 🎯 根因分析 · g1

### 因果链

```text
应用容器依赖的底层配置资源(CM/Secret)缺失 → 应用启动/初始化阶段抛出 CONFIG_MISSING → 进程以 exit_code 78 退出 → 容器进入 CrashLoopBackOff 状态且对外返回 500 错误
```

### 根因结论

根因已确认：**应用容器依赖的配置资源缺失导致启动失败**。
现有证据高度一致地支撑该结论：
1. **K8s 层面**：Pod 处于 `CrashLoopBackOff`，重启计数为 11，进程非正常退出（fact-4a81fe78b67a, fact-a544f7fa05ad, fact-1e1cb92a5992）。
2. **应用日志**：反复抛出 `CONFIG_MISSING` 错误并返回 HTTP 500（fact-604d69142d48）。
3. **链路追踪**：Deepflow 与 Tempo 联合证实了流量被拦截在 `500` 错误，且 Span 标记为 `config_missing_exit` 模式（fact-03150229f37a, fact-5888072297e4）。
证据链完整，无需补充决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 18.2s
├─ 并发证据采集: 45.1s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 45.1s (Evidence 38.1s, RCA 6.7s)
└─ 汇总总结: 12.1s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
