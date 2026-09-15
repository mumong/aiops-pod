## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod aiops-case-v08/workload 处于 CrashLoopBackOff 状态，无法正常运行 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Back-off restarting failed container app in pod workload_aiops-case-v08(00e5e755-886e-4661-9e8a-00d1e71595f6)` | 确认容器持续重启并被调度器强制 BackOff 的现场状态 |
| 2 | K8s State | container | `last_terminated_reason`: Error, `last_exit_code`: 127 | 确认容器以 127 异常码终止，这是命令或文件缺失的典型特征 |
| 3 | K8s Config | pod spec | `resource_request.memory`: 8Mi, `resource_limit.memory`: 32Mi | 资源请求极低，排除 OOMKill（OOMKill 通常退出码为 137），将根因指向应用逻辑 |
| 4 | Logging | elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | **决定性证据**：直接指出容器主进程执行 `/opt/app/unavailable-command` 失败 |
| 5 | K8s Event | pod | `Reason: CrashLoopBackOff` | 关联日志与事件，确立因启动命令缺失导致的循环重启现象 |

**证据互证说明**：
日志事实 (#4) 提供了容器启动失败的具体技术细节，解释了为何退出码为 127 (#2)。极低的内存限制 (#3) 与 127 退出码共同排除了资源耗尽（如 OOM）的可能性，确立了根因为“命令文件/二进制缺失”。事件 (#1, #5) 证实了这一单次失败演变为集群级持久性故障（CrashLoopBackOff）的结果。

## 🎯 根因分析 · g1

### 因果链
```text
容器镜像中缺失入口命令 /opt/app/unavailable-command → 容器主进程执行 sh -c exec 失败 (Exit Code 127) → Kubernetes 检测到容器持续重启并进入 BackOff 策略 → Pod 状态显示为 CrashLoopBackOff
```

### 根因结论
**已确认的根因**：
Pod `aiops-case-v08/workload` 中的 `app` 容器主进程启动失败。
根据 Elasticsearch 日志事实，容器尝试执行的命令 `/opt/app/unavailable-command` 在镜像中不存在 (`not found`)，导致 Shell 以退出码 127 报错。这一启动失败引发了 Kubelet 的持续重启尝试，最终因重启频率过高而触发 `BackOff` 状态。

支持该结论的关键事实：
1. 日志明确提示目标命令未找到 (logging fact)。
2. 容器终止状态为 Error 且退出码为 127 (kubernetes state fact)。

---

## 📊 性能统计

```text
├─ 总耗时: 53.8s
├─ 问题定位: 19.7s
├─ 并发证据采集: 24.7s
│  └─ g1 aiops-case-v08/workload: 24.7s (Evidence 17.7s, RCA 6.8s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
