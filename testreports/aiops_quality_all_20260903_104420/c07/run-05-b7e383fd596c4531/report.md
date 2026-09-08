## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Pod workload-dff5cbc6b-kmfxx 持续处于 CrashLoopBackOff 状态，Container app 重启 6 次，退出码 78，日志显示 CONFIG_MISSING 错误。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.waiting_reason: CrashLoopBackOff; container.last_terminated_reason: Error (fact-b90e5eb5aab0, fact-851e046ec1aa) | 确认容器因非零退出码反复被 K8s 终止，且处于重启退避状态。 |
| 2 | Logging | elasticsearch | 8 条 "CONFIG_MISSING" 错误日志，HTTP 500 响应，出现时间 13:59:02Z 至 14:05:34Z (fact-193f0aa6da93) | 直接指出故障原因为配置缺失，且日志与 HTTP 报错同步出现。 |
| 3 | Tracing | deepflow | L7 聚合流 10 次，GET /work 请求返回 HTTP 500 (src: 172.16.104.9 -> dst: 172.16.104.15)，与日志 trace_id 一致 (fact-522bcae1d3d8) | 从网络层观测到对等请求被拒绝，确认为应用逻辑故障而非 K8s 资源问题。 |
| 4 | K8s State | kubernetes | container.last_exit_code: 78 (fact-0b642117c48a) | 提供具体的应用层退出码，与 "CONFIG_MISSING" 现象匹配。 |
| 5 | K8s Event | kubernetes | BackOff 重启警告 (x21 over 8m16s)，确认重启频率在增加 (fact-e9f7fa244830) | 佐证重启循环持续且正在恶化。 |

K8s 状态证明容器不断重启，日志记录明确指出了应用层退出原因是 "CONFIG_MISSING"，而 Tracing 中的 L7 流和日志 trace_id 重合，证明该错误发生在应用处理请求的逻辑内部，且每次重启后都会复现。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖的配置项 (ConfigMap) 中缺少预期 key/value → 应用启动或初始化时主动校验失败 (exitCode=78, CONFIG_MISSING) → K8s 检测到容器非正常退出并触发重启策略 → Pod 持续处于 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因是应用启动时因找不到所需配置项（日志记录 `CONFIG_MISSING`）而主动退出（退出码 78）。证据包括：
- K8s 观测到容器反复以 Error 状态终止（fact-851e046ec1aa）；
- 日志记录显示 8 次因 `CONFIG_MISSING` 引发的 HTTP 500 错误（fact-193f0aa6da93）；
- 追踪数据确认请求在处理阶段直接失败（fact-b053da665df6）。

当前缺乏的决定性事实包括：ConfigMap `workload-code` 中具体缺失的 key 或 value 内容，以及应用代码中触发 `CONFIG_MISSING` 的具体逻辑路径。这些缺失不影响对“应用因配置缺失主动退出导致 CrashLoop”这一根因的判定。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 31.0s
├─ 并发证据采集: 89.6s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 89.6s (Evidence 77.5s, RCA 11.9s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
