## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod aiops-case-v08/workload 的启动命令 `command` 配置为 `sh -c exec /opt/app/unavailable-command`，该可执行文件在基础镜像中不存在。系统在容器启动时执行该命令失败（Exit Code 127），导致进程立即退出，kubelet 持续重启容器，最终引发 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | Kubernetes | `container.last_terminated_reason: Error` (`fact-00780edb1f6d`) | 确认容器退出原因 |
| 2 | K8s Config | Kubernetes | `container.waiting_reason: CrashLoopBackOff` (`fact-88c95c513799`) | 确认 Pod 当前异常状态 |
| 3 | K8s Config | Kubernetes | `container.last_exit_code: 127` (`fact-40a26ad17cfc`) | 指示程序文件缺失导致执行失败 |
| 4 | K8s Event | Kubernetes | `Back-off restarting failed container app` (`fact-8626d774d23a`) | 确认 kubelet 已进行多次重启尝试 |
| 5 | Logging | Elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` (`fact-13cb3242823d`) | 直接证明启动命令中引用的可执行文件不存在 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason=CrashLoopBackOff, value=1) (`fact-7c1ace59f1b2`) | 验证 Pod 等待状态指标 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total` (value=11) (`fact-c758eed8a777`) | 验证容器已重启次数，佐证启动失败并陷入循环 |

**证据分析：**
K8s 状态与日志证据形成闭环：Exit Code 127 (`fact-3`) 与 "not found" 错误日志 (`fact-5`) 共同指向应用二进制文件缺失，导致容器进程立即退出。K8s 事件 (`fact-4`) 与 Metric 重启计数 (`fact-7`) 证实了因此触发的重试机制已导致 Pod 进入 CrashLoopBackOff 状态 (`fact-2`)。Metric 中的 waiting reason (`fact-6`) 与状态指标一致，排除了其他指标维度冲突。

## 🎯 根因分析 · g1

### 因果链

```text
容器配置指定了镜像中不存在的可执行文件 /opt/app/unavailable-command → 执行 exec 时返回 Exit Code 127 并立即退出 → 容器状态变为 Error，kubelet 触发指数退避重启 → Pod 陷入 CrashLoopBackOff 循环
```

### 根因结论

已确认根因为：Pod `aiops-case-v08/workload` 中 `app` 容器的启动命令引用了不存在的可执行文件 `/opt/app/unavailable-command`。
该错误由直接观测到 `Exit Code 127` (`fact-3`) 以及日志中明确的 "not found" 信息 (`fact-5`) 所证实。由于容器启动失败，Kubelet 不断重启容器，导致 Pod 长期处于 `CrashLoopBackOff` 状态 (`fact-2`, `fact-6`)，且已累积 11 次重启 (`fact-7`, `fact-4`)。现有 Kubernetes 状态、日志与监控指标证据充分，根因明确。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.0s
├─ 并发证据采集: 37.2s
│  └─ g1 aiops-case-v08/workload: 37.2s (Evidence 29.3s, RCA 7.8s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime, pod-config-error
