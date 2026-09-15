## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod aiops-case-v10/workload 的容器 app 配置中缺失必需的环境变量 APP_REQUIRED_CONFIG。容器启动脚本通过 os.getenv 检查该变量，因值为 None 而打印错误日志并主动执行 sys.exit(78) 退出。该启动失败导致 kubelet 反复重启容器，最终进入 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: {"container": "app", "reason": "CrashLoopBackOff"} | 确证容器当前异常状态 |
| 2 | K8s Event | kubernetes | `event.message`: "Warning BackOff ... Back-off restarting failed container app in pod workload_aiops-case-v10(d3e0dc86-6f8b-4f29-a50c-826bf2a1f1e6)" (发生188次，持续41m) | 描述 kubelet 因容器反复启动失败而退避重启的行为模式 |
| 3 | K8s State | kubernetes | `container.last_terminated_reason`: {"container": "app", "reason": "Error"} | 确证上一次容器终止原因为 Error |
| 4 | K8s State | kubernetes | `container.last_exit_code`: {"container": "app", "exit_code": 78} | 记录导致终止的具体退出码，表明容器进程主动退出 |
| 5 | K8s Config | kubernetes | `container.resource_limit.memory`: "32Mi" | 提供容器资源限制上下文，排除显性资源超限（OOM）可能 |
| 6 | Logging | elasticsearch | `log.message`: "APP_REQUIRED_CONFIG environment variable is missing" | 直接揭示应用崩溃前的具体业务错误：缺失必需环境变量 |
| 7 | K8s State | kubernetes | `container.restart_count`: {"container": "app", "restart_count": 12} | 量化重启频率，证实持续性的启动失败 |
| 8 | Metric | prometheus | `kube_pod_container_status_restarts_total`: "12" | 验证 K8s 层面的重启计数 |

证据链中，K8s 状态与事件确认了 CrashLoopBackOff 的反复重启现象与具体 Exit 78 退出码；Elasticsearch 日志中的明确报错 `APP_REQUIRED_CONFIG environment variable is missing` 给出了 Exit 78 的直接业务原因；Prometheus 指标进一步佐证了重启计数。所有观测点一致指向应用启动配置缺失导致主动退出，进而引发 kubelet 崩溃重启。

## 🎯 根因分析 · g1

### 因果链

```text
缺少必需环境变量 APP_REQUIRED_CONFIG → 启动脚本 os.getenv 为 None 主动执行 sys.exit(78) → 容器启动失败 → CrashLoopBackOff
```

### 根因结论

已确认的根因为：Pod `aiops-case-v10/workload` 的容器 `app` 启动脚本在启动时检查环境变量 `APP_REQUIRED_CONFIG`，发现其值为 `None`，随后打印错误日志并主动以退出码 78 (`sys.exit(78)`) 退出进程。

该应用层的主动退出直接导致容器处于 `Error` 终止状态（证据 #3, #4），Kubelet 发现容器非正常退出后触发重启机制；由于根本原因（变量缺失）未解决，重启再次失败，最终导致容器在 `CrashLoopBackOff` 状态（证据 #1, #2）并持续累积重启次数（证据 #7, #8）。

---

## 📊 性能统计

```text
├─ 总耗时: 10.0m
├─ 问题定位: 23.3s
├─ 并发证据采集: 563.7s
│  └─ g1 aiops-case-v10/workload: 563.7s (Evidence 556.9s, RCA 6.7s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
