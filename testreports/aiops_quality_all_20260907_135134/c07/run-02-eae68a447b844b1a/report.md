## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | aiops-case-07/workload-dff5cbc6b-fkzvn 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `Back-off restarting failed container app in pod workload-dff5cbc6b-fkzvn_aiops-case-07` | 直接证实 CrashLoopBackOff 行为 |
| 2 | K8s State | `kubernetes` | `container.last_terminated_reason: Error` (Exit Code: 78) | 明确应用进程退出类型及系统级退出码 |
| 3 | K8s Config | `kubernetes` | `resource_limit.memory: 96Mi` (Request: 24Mi) | 排除 OOMKilled 或资源限制导致内存不足 |
| 4 | Logging | `elasticsearch` | `CONFIG_MISSING` (HTTP 500, path: `/work`, 10次) | 揭示业务层面的具体错误模式 |
| 5 | Tracing | `tempo` | `attributes.aiops.observed_mode: config_missing_exit`, 对应 trace_id `b3559561ac9acd05071836e31ce2b090` | 提供日志缺失时间点的业务逻辑闭环，确证退出机制 |
| 6 | Metric | `prometheus` | `kube_pod_container_status_last_terminated_reason: Error` (labels: `reason: Error`) | 辅助确认终止原因为应用异常而非系统层 |

**证据印证：**
K8s 层面 Exit Code 78 属于应用级致命错误，与 Logging 中的 `CONFIG_MISSING` 及 Tracing 中的 `observed_mode: config_missing_exit` 形成完整证据链，共同指向配置缺失导致的服务崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
关键配置文件缺失 → 应用启动读取配置失败抛出 CONFIG_MISSING → 进程以退出码 78 终止 → Kubelet 触发 CrashLoopBackOff
```

### 根因结论

**已确认的根因：应用关键配置文件缺失 (CONFIG_MISSING)**

应用进程因无法读取必要的配置文件而抛出 `CONFIG_MISSING` 错误，导致进程以退出码 78（应用级致命错误）终止。

- **事实支撑**：
    - 业务日志持续输出 `CONFIG_MISSING` 错误且伴随 HTTP 500（证据 #4）。
    - Tracing 数据（证据 #5）中 `aiops.observed_mode: config_missing_exit` 与日志模式一致，验证了这是导致退出的直接机制。
    - K8s 层面容器状态确认为 `Error` 且退出码为 78（证据 #2），排除了 OOMKilled 或系统资源限制（证据 #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 16.3s
├─ 并发证据采集: 109.2s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 109.2s (Evidence 101.2s, RCA 7.7s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
