## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | Application code fails to locate required configuration files during startup, resulting in exit code 78 and immediate crash. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: `CrashLoopBackOff` (fact-215ba18a4f19) | 确认 Pod 处于重启循环异常状态。 |
| 2 | K8s State | kubernetes | `container.last_exit_code`: `78` (fact-2611b1e9f7e1) | 明确应用进程的终止代码，指向启动阶段的特定退出逻辑。 |
| 3 | K8s Event | kubernetes | `BackOff restarting failed container app` (fact-221846d9ca89) | 记录 kubelet 因应用频繁退避而发出的警告事件。 |
| 4 | Logging | elasticsearch | `CONFIG_MISSING` 错误模式出现 8 次，时间范围 `14:01:02` 至 `14:21:14`，包含 `http_status: 500` (fact-80ca2256235b 等) | 直接暴露应用内部错误原因：在启动或处理请求时未找到配置文件。 |
| 5 | Tracing | deepflow | HTTP GET /work 返回 500，关联 trace_id: `1d3e3ac2e83ba2c98d762899d4db7ec5` 等，共 9 次 (fact-522bcae1d3d8 等) | 通过链路追踪证实 500 错误伴随上述日志模式重复出现。 |

**证据综合：**
- K8s 层面记录 Pod 因 `exit_code=78` 频繁重启，并处于 `CrashLoopBackOff` 状态。
- 日志维度明确指出失败机制为 `CONFIG_MISSING`，这与代码逻辑启动失败相符。
- 追踪维度确认了包含相同错误特征的外部访问请求均返回 500，进一步佐证了应用处于不可用且尝试启动失败的状态。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动逻辑缺失配置文件 → 触发 CONFIG_MISSING 错误 (exit 78) → Pod 异常终止并被 K8s 重启 → CrashLoopBackOff / 返回 500
```

### 根因结论

**已确认的根因**：应用代码在启动期间未能定位到所需的配置文件，导致进程以退出代码 `78` 终止。

这一结论由日志中的 `CONFIG_MISSING` 模式、日志中记录的高频 500 错误以及 K8s 中明确记录的 `exit_code: 78` 共同证实。Pod 因无法成功启动而进入 `CrashLoopBackOff` 循环。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 38.0s
├─ 并发证据采集: 76.8s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 76.8s (Evidence 71.5s, RCA 5.1s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
