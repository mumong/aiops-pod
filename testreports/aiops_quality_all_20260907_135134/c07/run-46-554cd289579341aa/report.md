## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | 应用代码在启动或请求阶段因检测到关键配置缺失（CONFIG_MISSING）而主动退出（Exit Code 78），导致容器反复崩溃并进入 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | 容器状态: `waiting_reason=CrashLoopBackOff`, `last_terminated_reason=Error` | 确立容器持续崩溃的异常事实 |
| 2 | K8s Event | `kubernetes` | `BackOff  9m13s (x377 over 94m)` 重启失败 | 确认崩溃处于 BackOff 延迟阶段，表明应用未自愈 |
| 3 | K8s State | `kubernetes` | 容器启动退出码: `exit_code: 78` | 直接反映应用非系统信号（如 OOMKilled）终止，而是应用层主动退出 |
| 4 | Logging | `elasticsearch` | 8次重复日志: `http_request level=error message="CONFIG_MISSING" path="/work" http_status=500` (时间: 2026-09-07 15:44:20 - 16:05:27) | 证明应用确实在请求处理或启动检查阶段检测到配置缺失并报错退出 |
| 5 | Tracing | `tempo` | Span: `aiops.observed_mode="config_missing_exit"`, `http.response.status_code=500` | 链路层面证实应用内部逻辑将配置缺失判定为启动或请求失败的直接原因 |
| 6 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason=1` (CrashLoopBackOff), `restart_count=22` | 从监控指标侧面印证了 K8s 状态和现象的持续性 |

**证据印证说明：**
- 证据 1、2、6 从 K8s 控制平面（状态、事件）和监控层确立了 `CrashLoopBackOff` 和频繁重启的现象。
- 证据 3 提供了退出码 `78`，排除了资源（如内存）导致系统杀进程（Exit 137）的可能性，指向应用逻辑。
- 证据 4 和 5 形成了闭环：日志显示应用因 `CONFIG_MISSING` 返回 500 错误，Tracing 中的 `config_missing_exit` 模式则揭示了导致该 500 错误并最终触发应用自杀（Exit 78）的内部机制。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置关键缺失 (CONFIG_MISSING) → 应用启动/请求阶段自检失败 → 应用主动异常退出 (Exit Code 78) → 容器进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为：**应用代码（启动或请求处理阶段）检测到关键配置缺失（`CONFIG_MISSING`），并主动返回 500 错误后退出（Exit Code 78）。**

该结论得到多维度事实支撑：
- **直接证据**：日志中的 `message="CONFIG_MISSING"` (证据 4) 与 Tracing 中的 `aiops.observed_mode="config_missing_exit"` (证据 5) 明确指出了失败的内部原因。
- **结果证据**：K8s 容器状态 `CrashLoopBackOff` (证据 1) 和退出码 `78` (证据 3) 证实应用是以可控但失败的方式终止，而非由外部资源限制或网络故障导致。

现有证据已充分覆盖因果链，无需补充更多事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 11.8s
├─ 并发证据采集: 85.9s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 85.9s (Evidence 78.2s, RCA 7.5s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
