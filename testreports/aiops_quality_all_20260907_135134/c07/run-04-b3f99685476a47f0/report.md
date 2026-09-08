## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Pod workload-dff5cbc6b-fkzvn 处于 CrashLoopBackOff 状态，容器反复重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `BackOff restarting failed container app` (fact-20d136c72cf2) | 确认 Kubernetes 因容器反复失败而执行指数退避重启策略。 |
| 2 | K8s State | `kubernetes` | `last_terminated_reason: Error`, `exit_code: 78` (fact-95edea47cc48, fact-93ab61fcf869) | 直接表明应用进程异常终止，非资源超限导致的 OOMKilled。 |
| 3 | K8s Config | `kubernetes` | `request.memory: 24Mi`, `limit.memory: 96Mi` (fact-0069d155dafe, fact-7a3e1aba274b) | 提供容器资源限制配置，用于排除资源不足导致的进程终止。 |
| 4 | Logging | `elasticsearch` | `CONFIG_MISSING` 错误模式重复 8 次，时间范围 `2026-09-07T14:35:23Z` 至 `14:41:46Z` (fact-...) | 指出导致进程终止的具体应用层原因为缺失配置项。 |
| 5 | Tracing | `tempo` | Trace `b3559561...` 显示 `aiops.observed_mode=config_missing_exit` 及 HTTP 500 (fact-0022d2f0ccba) | 关联具体链路确认应用因配置缺失主动退出。 |
| 6 | Tracing | `deepflow` | L7 Flow 聚合显示 `/work` 接口 9 次请求返回 500 状态 (fact-...) | 佐证应用持续抛出 500 错误并失败的行为模式。 |

**证据综合：**
Kubernetes 事件 (1) 证实 Pod 处于重启循环中。K8s 状态 (2) 与 Trace 上下文 (5) 共同锁定了终止原因为应用逻辑异常（退出码 78 且标记为 config_missing_exit），而非 Kubernetes 基础设施问题。日志模式 (4) 进一步将根因具体化为“缺失配置”，且 Trace 的 HTTP 请求 (6) 与日志时间窗口高度一致，形成完整证据链。

## 🎯 根因分析 · g1

### 因果链

```text
缺失配置依赖 → CONFIG_MISSING 异常抛出并返回 HTTP 500 → 进程以 exit code 78 终止 → Kubernetes 触发 CrashLoopBackOff 重启机制
```

### 根因结论

**已确认的根因：**
Pod `workload-dff5cbc6b-fkzvn` 中的 `app` 容器因**应用程序配置缺失**导致启动或运行时逻辑失败。应用代码抛出 `CONFIG_MISSING` 错误并返回 HTTP 500 状态码，直接导致进程以**退出码 78** 非正常终止（证据 2, 4, 5）。由于容器以非零码退出，Kubernetes 识别到容器失败并进入 `CrashLoopBackOff` 状态进行反复重启（证据 1, 3）。

**未知与局限：**
输入事实中未提供缺失的具体配置 Key 名称（如 `fact-unknowns` 所示），也未包含 `ConfigMap workload-code` 的详细内容以对比预期配置与实际内容的差异细节。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 13.3s
├─ 并发证据采集: 86.3s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 86.3s (Evidence 77.0s, RCA 9.1s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
