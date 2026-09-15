## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod aiops-case-v10/workload 处于 CrashLoopBackOff 状态，容器 app 反复以 Exit Code 78 退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | K8s | `Warning BackOff ... Back-off restarting failed container app` | 确认容器进入 CrashLoopBackOff 状态 |
| 2 | K8s State | K8s | `container.last_exit_code`: `78` | 应用主动退出，非资源驱逐 |
| 3 | Logging | ES | `APP_REQUIRED_CONFIG environment variable is missing` | 揭示应用崩溃的直接业务原因 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (`CrashLoopBackOff`) | 指标确认 Pod 当前处于等待重启状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` = 1 (`Error`) | 与 K8s Event 的 Error 状态一致 |

**证据分析：**
日志 Fact-1aeaadf9bbec 直接指出缺少 `APP_REQUIRED_CONFIG` 环境变量，这解释了为何进程以非 OOM 的退出码 78 终止。Metric Fact-ff2d2b19a485 和 K8s Event Fact-16a72f768b1b 共同确认了 Pod 目前处于 CrashLoopBackOff 阶段，且无资源限制（CPU 50m / Memory 32Mi）相关的 OOMKilled 证据。

## 🎯 根因分析 · g1

### 因果链

```text
环境变量 APP_REQUIRED_CONFIG 缺失 → 容器启动命令执行 getenv 检查失败并执行 sys.exit(78) → 容器以 Error 状态终止且无 OOMKilled 或探针杀死事件 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为：**容器主进程启动命令中依赖的环境变量 `APP_REQUIRED_CONFIG` 未注入，导致应用主动检测失败并退出（Exit Code 78）。**

- **证据支持**：日志 Fact-1aeaadf9bbec 明确记录了缺失该环境变量的信息；同时，容器退出码为 78（Fact-4a978dcbf41f）且 Metric 显示终止原因为 Error（Fact-697bc46ed7e0），排除了资源限制或健康检查探针超时等常见原因，确认是应用内部逻辑校验失败。
- **状态说明**：当前 Pod 处于 CrashLoopBackOff 状态（Fact-ff2d2b19a485），由于缺少必要配置，重启将继续失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.0s
├─ 并发证据采集: 53.1s
│  └─ g1 aiops-case-v10/workload: 53.1s (Evidence 45.1s, RCA 7.9s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
