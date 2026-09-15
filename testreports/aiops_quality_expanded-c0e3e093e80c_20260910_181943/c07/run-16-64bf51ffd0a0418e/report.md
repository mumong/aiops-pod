## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Container 'app' crashes with exit code 78 due to a 'CONFIG_MISSING' error. This application-level failure is observed consistently across recent logs, tracing, and pod termination reasons, causing the CrashLoopBackOff state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Container 'app' `exit_code`: 78, `waiting_reason`: CrashLoopBackOff | 确认异常实体的持续故障现象 |
| 2 | K8s Event | kubernetes | `BackOff restarting failed container app` (132 times over 31m) | 确认异常实体的启动失败与重试频率 |
| 3 | K8s State | kubernetes | Pod `ContainersReady`: False, 容器状态 `reason`: Error | 排除调度与资源瓶颈，确认应用容器终止 |
| 4 | Logging | elasticsearch | Pattern `CONFIG_MISSING` (HTTP 500, `/work`) 出现 8 次，`allocated_mib` 均为 0 | 直接定位导致崩溃的应用层错误类型 |
| 5 | Tracing | DeepFlow | L7 Flow `GET /work` 响应 `500`，请求从 `172.16.104.8` 发往 Pod IP `172.16.104.63` | 确认故障发生在应用处理请求阶段，排除网络传输层问题 |
| 6 | Tracing | Tempo | Span `GET /work` 属性 `aiops.observed_mode: config_missing_exit` | 将日志与具体应用行为映射，验证崩溃原因的一致性 |

证据显示，日志中持续的 `CONFIG_MISSING` 报错与 Trace 中的 `config_missing_exit` 模式高度一致，且 `allocated_mib` 始终为 0，证明应用并非因内存不足被 OOMKilled，而是由于配置缺失触发了应用内部的致命错误（退出码 78），导致 K8s 持续进行 Restart 操作。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置缺失 (LOGGING/TRACEING) → 应用逻辑终止并返回错误退出码 (K8s/Metrics) → CrashLoopBackOff (K8s State)
```

### 根因结论

**已确认的根因**：应用容器 `app` 崩溃的直接原因是**配置缺失（CONFIG_MISSING）**。
1. 应用在处理 `GET /work` 请求时，因未能找到所需配置直接触发内部错误，记录日志 `CONFIG_MISSING` 并返回 HTTP 500。
2. Trace 数据中的 `aiops.observed_mode: config_missing_exit` 明确印证了应用是在检测到配置缺失后主动终止（对应 Pod 退出码 78）。
3. K8s 状态显示 Pod 持续重启（`CrashLoopBackOff`），这是由于容器异常退出后由 kubelet 触发重启机制所致。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 19.3s
├─ 并发证据采集: 70.9s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 70.9s (Evidence 63.6s, RCA 7.1s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
