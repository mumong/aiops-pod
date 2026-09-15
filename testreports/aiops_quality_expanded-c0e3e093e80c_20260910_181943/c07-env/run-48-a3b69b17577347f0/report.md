## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod aiops-case-v10/workload 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `CrashLoopBackOff` (fact-640ec63c1e17) | 确认 Pod 处于失败重启状态 |
| 2 | K8s Event | Kubernetes | `BackOff` 事件，重复 398 次，持续 85m (fact-9b11976e6894) | 佐证应用处于持续且频繁的 CrashLoop 循环中 |
| 3 | K8s State | Kubernetes | `container.last_terminated_reason`: `Error`, `container.last_exit_code`: `78` (fact-a9df99adab85, fact-278edcba889a) | 指出容器以特定非零代码异常终止 |
| 4 | Logging | Elasticsearch | `APP_REQUIRED_CONFIG environment variable is missing` (fact-26f5061a7001) | 直接指出导致退出的具体缺失条件 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: `21` (fact-24acd21aea56) | 量化确认重启频次，符合 CrashLoopBackOff 现象 |
| 6 | K8s Config | Kubernetes | `resource_limit.memory`: `32Mi`, `resource_limit.cpu`: `50m` (fact-802f3b8bb1b0, fact-2bfbad80ea78) | 排除资源硬限制导致 OOM/CPU Throttling 的可能性 |

**证据关联与印证：**
日志中报告环境变量缺失 (Evid #4) 与容器异常退出码 `78` (Evid #3) 形成直接的因果关系。Pod 的持续状态 `CrashLoopBackOff` 及大量 `BackOff` 事件 (Evid #1, #2) 证实了该异常终止机制触发了指数退避重启，最终形成了持续 85 分钟、重启 21 次的循环 (Evid #5)。资源限制配置较低 (Evid #6) 但并非触发点，排除了资源瓶颈导致崩溃的可能。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义缺失环境变量 APP_REQUIRED_CONFIG → 容器启动脚本检测到变量缺失并触发 sys.exit(78) → 容器以 Error 状态终止并触发 K8s 指数退避重启机制 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认的根因**是：容器应用启动逻辑强依赖环境变量 `APP_REQUIRED_CONFIG`，但 Pod 定义中未提供该变量，导致应用进程启动即退出，退出码为 `78`。

该结论由以下事实确凿支撑：
- **直接诱因**：日志明确记录 `APP_REQUIRED_CONFIG environment variable is missing` (Evid #4)。
- **后果验证**：Kubernetes 捕获到终止原因为 `Error` 且退出码为 `78` (Evid #3)，随后立即触发重试。
- **系统状态**：Kubelet 记录的大量 `BackOff` 事件及 21 次重启计数 (Evid #1, #2, #5) 验证了“启动即失败”的循环现象。

现有证据链条完整，无需其他维度的决定性事实即可闭环。

---

## 📊 性能统计

```text
├─ 总耗时: 50.0s
├─ 问题定位: 15.6s
├─ 并发证据采集: 23.1s
│  └─ g1 aiops-case-v10/workload: 23.1s (Evidence 16.2s, RCA 6.8s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
