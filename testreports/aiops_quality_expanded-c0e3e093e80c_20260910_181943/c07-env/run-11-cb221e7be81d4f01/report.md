## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Warning BackOff: "Back-off restarting failed container app in pod workload_aiops-case-v10" (x49) | 确认为持续性 CrashLoopBackOff 异常状态 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason`: Error, `exit_code`: 78, `restart_count`: 7 | 确认容器因 Error 终止且退出码 78 |
| 3 | Logging | elasticsearch | "APP_REQUIRED_CONFIG environment variable is missing" | 定位应用主动因配置缺失退出的直接原因 |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory`: 32Mi, `container.resource_request.memory`: 8Mi | 排除资源限制导致的 OOMKilled |
| 5 | K8s Config | kubernetes | `container.resource_limit.cpu`: 50m, `container.resource_request.cpu`: 5m | 排除 CPU 限制导致的 throttling |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: 1 (reason: CrashLoopBackOff); `kube_pod_container_status_restarts_total`: 7 | 指标数据与 K8s 状态完全一致 |

**证据印证说明：**
日志中 `APP_REQUIRED_CONFIG` 缺失直接解释了容器为何以退出码 78 主动退出（Error），结合 K8s 事件与 Metrics 的 7 次重启记录，证实了应用因缺少启动依赖配置陷入 CrashLoopBackOff 循环。资源配置检查（内存/计算）均非导致退出的原因。

## 🎯 根因分析 · g1

### 因果链

```text
容器定义中未配置 APP_REQUIRED_CONFIG 环境变量 → 应用启动脚本检测变量缺失并主动退出（sys.exit(78)） → 容器以 Error 状态终止 → kubelet 触发 CrashLoopBackOff 重启循环
```

### 根因结论

**已确认根因**：容器定义中缺失应用启动必需的 `APP_REQUIRED_CONFIG` 环境变量。
应用进程在启动时检测到该配置缺失，主动调用 `sys.exit(78)` 退出。该退出行为（退出码 78）被 kubelet 识别为异常（Error），进而触发 CrashLoopBackOff 重启机制。此结论由日志事实（fact-1aeaadf9bbec）直接证实，并被容器退出码事实（fact-0f88bb482303）和重启计数事实（fact-2ed3e263c104）交叉验证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 31.4s
├─ 并发证据采集: 37.2s
│  └─ g1 aiops-case-v10/workload: 37.1s (Evidence 28.9s, RCA 8.2s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
