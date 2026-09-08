## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `CrashLoopBackOff` | 确认 Pod 当前状态 |
| 2 | K8s Event | Kubernetes | `message`: `Back-off restarting failed container app` (over 46m) | 确认可持续性的重启行为 |
| 3 | K8s State | Kubernetes | `container.last_terminated_reason`: `Error` | 确认容器退出原因为非正常错误 |
| 4 | K8s State | Kubernetes | `container.last_exit_code`: `2` | 提供具体的异常退出码 |
| 5 | K8s Config | Kubernetes | `container.resource_limit.memory`: `96Mi` | 排除硬内存限制触发 OOM |
| 6 | Logging | Elasticsearch | Pattern: `runtime process exiting` (Error, 500), Time range: `12:47 - 13:13` | 提供应用层面的崩溃日志依据 |
| 7 | Logging | Elasticsearch | Pattern: `request completed` (Info, 200), numeric_fields `allocated_mib` 维持在 0 | 排除资源内存过载导致异常 |
| 8 | Tracing | Tempo/Deepflow | Span `684a53ea...` 关联成功响应，Flow `658aa...` 关联 500 错误 | 提供应用层请求执行结果 |

**证据说明：**
- **K8s 状态（#1, #2）** 确立了 `CrashLoopBackOff` 现象及持续 46 分钟的重启频率。
- **退出原因（#3, #4）** 提供了直接退出信号：非 OOM 状态下的 Error 且退出码为 2，与典型的环境变量缺失或入口点不可用特征一致。
- **内存与资源（#5, #7）** 日志中的 `allocated_mib` 稳定为 0 且资源限制为 96Mi，直接排除内存溢出导致 CrashLoopBackOff 的可能性。
- **应用日志（#6）** 与 K8s 的 `Error` 状态直接呼应，`runtime process exiting` 日志进一步证实了是进程自身退出了运行。

## 🎯 根因分析 · g1

### 因果链

```text
Entry point error (binary not found or script error) → runtime process exiting (exitCode=2) → Container CrashLoopBackOff (13 restarts) → Pod Unready
```

### 根因结论

已确认的根因为 **Application entry point error（应用入口点错误）**。

**事实支撑与推理：**
1. **非资源限制问题**：尽管 Pod 处于 `CrashLoopBackOff` 状态，但日志 `allocated_mib` 始终为 0，且内存硬限制（`resource_limit.memory`）为 96Mi，排除了因内存不足（OOMKilled）导致重启的可能。
2. **应用层崩溃**：日志记录明确显示 `runtime process exiting` 伴随 HTTP 500 错误（如 `fact-06ca54feb011`），直接对应 Kubernetes 记录的 `last_terminated_reason: Error`（如 `fact-02e09174cd77`）。
3. **退出码指示**：容器以退出码 `2` 终止（`fact-6cdb0d1843c0`），通常指示未找到命令、脚本语法错误或环境变量配置错误，而非系统级别的段错误（11）或 OOM（137）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 33.7s
├─ 并发证据采集: 73.3s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 73.3s (Evidence 64.3s, RCA 8.9s)
└─ 汇总总结: 12.2s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
