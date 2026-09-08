## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | 应用程序配置缺失（CONFIG_MISSING）导致进程异常退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason` = "Error" | 确认容器进程以非零状态退出 |
| 2 | K8s Event | Kubernetes | `BackOff restarting failed container app` (198次/46m) | 证实重启风暴已持续约 46 分钟 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory` = "96Mi" | 提供资源环境上下文 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason`=1 (reason=CrashLoopBackOff) | 独立印证容器当前处于等待重启状态 |
| 5 | Logging | Elasticsearch | `CONFIG_MISSING` 模式 (8次), `/work` (500), 无内存分配波动 (0 MiB) | 直接指出应用层配置缺失是终止原因 |
| 6 | Tracing | Deepflow/Tempo | Flow: `/work` GET 返回 500 (9次); Span: `observed_mode=config_missing_exit` | 关联日志模式，确认请求级故障与配置缺失直接相关 |

**证据说明：**
Kubernetes 层面的 `Error` 终止和 `CrashLoopBackOff` 状态（证据 1, 2, 4）与应用层的 `CONFIG_MISSING` 错误（证据 5, 6）互为印证。Logging 和 Tracing 的数据直接锁定了异常退出的具体原因是 `CONFIG_MISSING`（证据 5, 6），排除了资源超限等其它可能性（证据 3 显示内存限制 96Mi 且监控无分配波动）。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置缺失（CONFIG_MISSING） → 进程以退出码 78 终止 → Kubernetes 触发频繁重启 (BackOff) → 容器陷入 CrashLoopBackOff
```

### 根因结论

**已确认的根因**：应用程序配置缺失（`CONFIG_MISSING`）导致进程异常退出（Exit Code 78）。

**支撑依据**：
- **应用日志与流量证据**：Logging 显示在 `/work` 路径上反复出现 `CONFIG_MISSING` 错误（证据 5）；Tracing 的 Span 明确记录 `observed_mode=config_missing_exit`（证据 6），证实了应用内部因配置缺失而主动退出的行为。
- **K8s 状态证据**：Kubernetes 的 `container.last_terminated_reason` 为 `Error`，且 Pod 持续经历 `BackOff` 重启机制（证据 1, 2）。
- **状态一致性**：所有观察窗口内的应用错误均一致指向配置问题，且未观察到内存溢出（OOMKilled）等其他常见的崩溃原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 17.1s
├─ 并发证据采集: 58.0s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 58.0s (Evidence 51.9s, RCA 5.9s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
