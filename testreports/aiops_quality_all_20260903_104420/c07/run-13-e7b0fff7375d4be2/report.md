## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | 应用配置缺失（CONFIG_MISSING） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason: Error` | 直接证明应用容器非正常退出，符合配置缺失导致的启动失败特征 |
| 2 | K8s Event | kubernetes | `Warning BackOff restarting failed container app` (x89 over 22m) | 证实集群因容器反复崩溃触发指数退避机制，处于 CrashLoopBackOff 状态 |
| 3 | K8s State | kubernetes | `container.last_exit_code: 78` | 退出码 78 通常关联特定的应用级异常（如配置不可用），与日志错误码一致 |
| 4 | K8s Config | kubernetes | `cpu request: 20m / limit: 200m; memory request: 24Mi / limit: 96Mi` | 证明该容器资源配额设定合理，排除因 OOMKill 或 CPU Throttling 导致重启的可能 |
| 5 | K8s State | kubernetes | `container.restart_count: 9` | 确认异常处于持续发生的状态，与 22 分钟的 BackOff 时间窗口吻合 |
| 6 | Logging | elasticsearch | `CONFIG_MISSING` (error, path: /work, http_status: 500) (8 occurrences) | 在应用层直接定位到根因为“配置缺失”，明确错误性质 |
| 7 | Tracing | tempo | `GET /work` response_code: 500, `aiops.observed_mode: config_missing_exit` | 追踪数据确认应用在处理请求时主动退出（Exit），且观察到 16ms-27ms 的短耗时，表明应用启动后立即终止 |

**证据印证说明：**
日志（#6）与追踪数据（#7）在应用层形成闭环，明确指向 `CONFIG_MISSING` 是触发应用退出的原因；Kubernetes 的 `BackOff` 事件（#2）和退出码 78（#3）是应用层异常在基础设施层面的直接映射。资源配置（#4）排除了资源争抢作为干扰项。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置缺失（CONFIG_MISSING） → 容器启动检查配置失败，主动退出(Exit Code 78) → kubelet 持续尝试重启并触发 BackOff → 应用处于 CrashLoopBackOff 状态，无法提供服务
```

### 根因结论

已确认根因为 **应用配置缺失（CONFIG_MISSING）**。

该结论由以下事实支撑：
1.  **应用层直接证据**：日志记录了 `CONFIG_MISSING` 错误（证据#6），追踪跨度显示应用以 `config_missing_exit` 模式退出 HTTP 500 响应（证据#7）。
2.  **基础设施映射一致**：容器启动失败（Evidence#1）、应用退出码 78（Evidence#3）以及 Kubernetes 的 `CrashLoopBackOff` 事件（Evidence#2）完全符合配置错误导致应用无法启动的行为模型。
3.  **排除其他原因**：资源请求与限制设定正常（证据#4），无 OOM 迹象。

**未确认事实**：
具体缺失的是哪一个 ConfigMap Key 或环境变量未定义（即 `unknowns` 中提到的内容），当前证据仅确认了存在缺失的配置项，但未指出具体字段名。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 24.8s
├─ 并发证据采集: 59.6s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 59.6s (Evidence 53.7s, RCA 5.8s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
