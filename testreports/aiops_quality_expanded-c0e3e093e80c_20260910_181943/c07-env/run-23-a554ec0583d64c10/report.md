## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod workload in CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | Kubernetes | `container.resource_limit.memory`: 32Mi | 确认资源限制，排除硬限制OOM |
| 2 | K8s Config | Kubernetes | `container.resource_request.memory`: 8Mi | 确认资源申请基线 |
| 3 | K8s State | Kubernetes | `container.waiting_reason`: CrashLoopBackOff | 确认容器进入死循环重启状态 |
| 4 | K8s State | Kubernetes | `container.last_terminated_reason`: Error | 确认上次退出非正常 |
| 5 | K8s State | Kubernetes | `container.last_exit_code`: 78 | 确认进程异常退出的具体状态码 |
| 6 | K8s Event | Kubernetes | `kubelet`: Back-off restarting failed container app (212 over 46m) | 确认长时间重启失败及指数退避行为 |
| 7 | Logging | Elasticsearch | `log.message`: "APP_REQUIRED_CONFIG environment variable is missing" | 确认导致退出的具体业务错误原因 |
| 8 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (1, reason=CrashLoopBackOff) | 独立确认集群层面的状态为等待重启 |

证据分析：
1. 日志（证据#7）直接指出了应用启动失败的原因是缺少关键环境变量 `APP_REQUIRED_CONFIG`。
2. 容器退出码（证据#5）为 78，结合日志信息，该异常退出码即为应用未检测到配置变量后的行为结果。
3. Kubernetes 事件与状态（证据#3, #4, #6）证实了由于每次启动均失败（退出码 78），Kubelet 触发了 CrashLoopBackOff 机制，且该状态持续约 46 分钟。
4. 资源限制（证据#1）确认内存硬限制为 32Mi，排除 OOMKilled 的可能性，且 Metric（证据#8）进一步印证了当前的崩溃状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 中缺少关键环境变量 APP_REQUIRED_CONFIG → 容器应用启动时检测到配置缺失异常退出（exit_code 78） → Kubelet 持续重启触发指数退避机制导致 CrashLoopBackOff → 用户 Pod 无法就绪（Status: CrashLoopBackOff, Reason: Error）
```

### 根因结论

已确认根因为 **应用配置缺失**。

Pod `workload` 中的 `app` 容器因启动脚本/逻辑检测到缺失 `APP_REQUIRED_CONFIG` 环境变量（证据#7），以 `exit_code 78`（证据#5）非正常退出。该异常导致 Kubelet 不断重启容器并进入 `CrashLoopBackOff` 状态（证据#3, #6, #8）。

现有证据已构成完整的闭环，故障根因明确。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 16.4s
├─ 并发证据采集: 37.4s
│  └─ g1 aiops-case-v10/workload: 37.4s (Evidence 30.5s, RCA 6.8s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
