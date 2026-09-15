## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod 容器 app 启动脚本中强制依赖环境变量 `APP_REQUIRED_CONFIG`，但 Pod YAML 配置中该变量缺失，导致容器启动时立即以 Exit Code 78 退出，进而触发 Kubernetes 的重启退避机制进入 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff` (fact-3186d1ee9363) | 确定当前 Pod 容器处于重启退避等待状态 |
| 2 | K8s Event | Kubernetes | `BackOff: Back-off restarting failed container app in pod workload_aiops-case-v10(d3e0dc86-6f8b-4f29-a50c-826bf2a1f1e6)` (fact-31f68f1f3bcb) | 证实容器频繁重启并进入指数退避阶段 |
| 3 | K8s State | Kubernetes | `container.last_terminated_reason: Error`, `exit_code: 78` (fact-892ab463e801, fact-7cceaaed7079) | 明确最后一次容器终止原因为错误，且退出码为 78 |
| 4 | Logging | Elasticsearch | `log.message: APP_REQUIRED_CONFIG environment variable is missing` (fact-1aeaadf9bbec) | 提供具体的启动失败原因：强制依赖的环境变量缺失 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason[1]: 1` (CrashLoopBackOff) (fact-06cbed4f30a4) | 确认当前仍有 1 个容器处于 CrashLoopBackOff 状态 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total[1]: 6` (fact-54a112e08ef0) | 确认容器已重启 6 次，与 K8s 状态记录一致 |
| 7 | K8s Config | Kubernetes | `container.resource_limit.memory: 32Mi` (fact-63e0ed96b00b), `container.resource_limit.cpu: 50m` (fact-b3823467f224) | 提供资源配置上下文，排除资源耗尽导致 OOM/CPUThrottled 的可能性 |

Kubernetes 状态与指标数据高度一致，均显示容器处于 CrashLoopBackOff 且重启次数不断累积。日志明确记录了容器启动期间遇到的致命错误（缺少环境变量），而资源配置正常，这直接指向了应用配置层面的启动逻辑缺陷。

## 🎯 根因分析 · g1

### 因果链

```text
YAML 配置缺失 `APP_REQUIRED_CONFIG` 环境变量 → 容器启动脚本因强制依赖校验失败 → 进程以 Exit Code 78 退出并报错 "environment variable is missing" → Kubernetes 持续重启触发 BackOff 进入 CrashLoopBackOff 状态
```

### 根因结论

根因为 **Pod 配置中缺失启动脚本强依赖的关键环境变量**。
具体表现为：Pod 中 `workload` 容器启动时需读取 `APP_REQUIRED_CONFIG`，但该变量未在 YAML 中定义，导致应用启动立即失败（Exit Code 78，见证据 3、4）。Kubernetes 重启机制不断尝试启动，最终因重启过快被强制进入退避等待状态（证据 1、2、5、6）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 14.6s
├─ 并发证据采集: 35.0s
│  └─ g1 aiops-case-v10/workload: 35.0s (Evidence 28.8s, RCA 6.0s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
