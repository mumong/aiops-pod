## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod workload in aiops-case-v08 is stuck in CrashLoopBackOff state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.last_terminated_reason: Error | 确认容器上一次终止的具体原因分类 |
| 2 | K8s State | kubernetes | container.last_exit_code: 127 | 确定容器退出时的系统级原因 |
| 3 | Logging | elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 直接捕获导致进程无法启动的报错文本 |
| 4 | K8s Event | kubernetes | Warning BackOff, message: "back-off 5m0s restarting failed container=app pod=workload_aiops-case-v08" | 证实 Kubernetes 已经检测到重启循环并进入退避等待状态 |

上述 K8s 状态与日志证据互相印证：进程在尝试执行 `/opt/app/unavailable-command` 时因找不到命令（Exit Code 127）而直接终止，Kubelet 捕获该错误后触发重试机制，最终导致 Pod 停留在 CrashLoopBackOff 状态。

## 🎯 根因分析 · g1

### 因果链

```text
容器配置了指令 /opt/app/unavailable-command（不存在） → 容器运行时尝试启动进程失败（Exit Code 127） → Kubelet 连续重启失败并进入退避等待 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为：`容器配置的执行指令 `/opt/app/unavailable-command` 在当前容器镜像中不存在`。

该错误直接导致容器进程以 Exit Code 127 终止，K8s 持续重启容器从而形成循环。决定性证据为日志中的 `not found` 错误（见证据 #3）及 K8s 状态中的 `exit_code: 127`（见证据 #2）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 16.8s
├─ 并发证据采集: 42.8s
│  └─ g1 aiops-case-v08/workload: 42.8s (Evidence 34.1s, RCA 8.6s)
└─ 汇总总结: 6.5s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
