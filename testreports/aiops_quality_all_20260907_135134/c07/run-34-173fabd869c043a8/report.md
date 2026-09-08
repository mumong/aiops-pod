## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Pod CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.waiting_reason="CrashLoopBackOff", restart_count=18, last_exit_code=78 | 确认应用反复退出并进入重启循环的直接状态 |
| 2 | K8s Event | kubernetes | "Back-off restarting failed container app" (x310 over 72m) | 确认重启行为是持续且长期的 |
| 3 | Logging | elasticsearch | pattern: `{"event":"http_request","level":"error","message":"CONFIG_MISSING","http_status":500}`, occurrence=8, time: 15:23:32 - 15:44:22 | 确认应用进程在运行期间因配置缺失主动报错退出 |
| 4 | Tracing | tempo/deepflow | trace_id: 18ee938af7a7760fb6dca999c257c60f, span: "GET /work", response_code=500, attributes: `aiops.observed_mode="config_missing_exit"` | 确认日志模式对应的具体请求链路及退出模式 |

**证据关联说明：**
- 证据 1 的 `exit_code=78` 与证据 3 的 `CONFIG_MISSING` 错误日志直接对应，解释了 K8s 层面 Terminated 的原因。
- 证据 4 提供了具体流量级别的佐证，`aiops.observed_mode="config_missing_exit"` 属性精确复现了日志中的错误场景，并关联了特定的 Trace ID。
- 证据 2 的 BackOff 事件证实了由于上述持续的错误机制，Kubernetes 正在执行指数级退避的重启策略。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-code' 缺失应用所需键值 → 应用启动/处理请求时检测到 CONFIG_MISSING 并主动退出 (exit 78) → Pod 异常 Terminated → Kubelet 重启 Pod 进入 CrashLoopBackOff
```

### 根因结论

已确认的根因为：**应用因配置缺失（CONFIG_MISSING）主动退出导致 CrashLoopBackOff。**

证据 1 显示容器反复以退出码 78 终止，进入等待重启状态（CrashLoopBackOff）。证据 3 和 4 在日志和链路追踪中发现了明确的 `CONFIG_MISSING` 错误模式及 `config_missing_exit` 运行模式属性，证实应用并非因资源不足或网络问题崩溃，而是因为无法获取运行所需的环境配置。

未确认因素：缺失配置项在 ConfigMap `workload-code` 中的具体 Key 名。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 19.9s
├─ 并发证据采集: 73.5s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 73.5s (Evidence 63.5s, RCA 9.9s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
