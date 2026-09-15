## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod aiops-case-v08/workload 持续处于 CrashLoopBackOff 状态，容器 app 反复启动并立即退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.last_terminated_reason: Error | 确认容器上一次退出状态异常 |
| 2 | K8s Event | kubernetes | BackOff 56s (x72 over 16m) | 观测到 72 次重启失败及退避行为 |
| 3 | Logging | elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 明确指出启动时找不到可执行命令 |
| 4 | K8s State | kubernetes | container.last_exit_code: 127 | Exit Code 127 确证为“命令未找到”类系统错误 |
| 5 | Metric | prometheus | kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"}: 1 | 当前处于等待重试阶段，印证持续故障状态 |

**证据互证说明：**
日志中的“not found”错误（证据 3）与 Linux 系统约定的 Exit Code 127（证据 4）直接对应，证实故障发生机制为“找不到命令”。K8s 事件和指标（证据 2, 5）则证实了该启动失败导致了持续的 CrashLoopBackOff 循环。

## 🎯 根因分析 · g1

### 因果链

```text
容器配置不存在的命令 → 命令未找到 (not found) → 进程以 Exit Code 127 退出 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因为 **容器配置中指定了不存在的命令 `/opt/app/unavailable-command`**。

这一错误配置直接导致容器在启动时尝试执行该文件失败，系统返回 Exit Code 127（证据 4），并输出“not found”错误信息（证据 3）。kubelet 检测到该非零退出状态后，不断重启容器并触发 BackOff 策略，最终导致 Pod 呈现 CrashLoopBackOff 状态（证据 2, 5）。现有证据（日志、退出码、事件）已充分支撑该结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 42.9s
├─ 并发证据采集: 57.0s
│  └─ g1 aiops-case-v08/workload: 57.0s (Evidence 48.1s, RCA 8.8s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime, pod-oomkilled, pod-config-error
