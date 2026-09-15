## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod workload (aiops-case-v08) 持续处于 CrashLoopBackOff 状态，容器 app 反复启动失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Logging | Elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 提供进程直接崩溃原因，确认为“命令未找到” (Command not found)。 |
| 2 | K8s State | Kubernetes | `exit_code: 127`, `last_terminated_reason: Error` | 验证退出码 127 与命令缺失逻辑一致；终止原因为 Error 而非 OOMKilled。 |
| 3 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff`, `container.waiting_message: back-off 5m0s restarting failed container=app` | 解释 Pod 无法恢复运行并陷入指数退避的重启循环。 |
| 4 | K8s State | Kubernetes | `pod.phase: Running`, `container.restart_count: 12` | 确认 Pod 底层调度已就绪（Running），异常仅由单容器反复失败导致。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason(CrashLoopBackOff) = 1` | 跨维度印证 K8s 状态，确认容器当前正处在 BackOff 等待状态。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 12` | 量化重启次数，与 K8s `restart_count` 完全对齐。 |

**证据关系说明：**
- **日志与 K8s 退出状态的因果印证**：日志中 `/opt/app/unavailable-command: not found` 直接解释了 `exit_code: 127` 的来源，确立了主进程启动失败的根本原因。
- **现象与指标的一致**：`CrashLoopBackOff` 的 K8s 事件/状态与 Prometheus 指标相互印证，排除了网络或调度故障（Pod 为 Running 状态），将问题严格锁定在应用容器生命周期内。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 入口命令配置引用了镜像中不存在的可执行文件 (/opt/app/unavailable-command) → 容器主进程启动执行失败 (Exit Code 127) → Kubernetes 检测到非正常退出并触发自动重启 → 频繁重启触发退避机制导致 CrashLoopBackOff
```

### 根因结论

已确认的根因为：**Pod 入口命令配置引用了镜像中不存在的可执行文件**。

该配置缺陷导致容器主进程在启动阶段立即因“命令未找到” (Exit Code 127) 而崩溃。Kubernetes 随即触发重启机制，由于重启频率过快，系统将其降级为 `CrashLoopBackOff` 状态以避免资源浪费。日志证据 (`sh: exec: ... not found`) 与退出码事实 (`127`) 形成了完整的闭环证据链。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.9s
├─ 并发证据采集: 35.2s
│  └─ g1 aiops-case-v08/workload: 35.2s (Evidence 24.9s, RCA 10.2s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
