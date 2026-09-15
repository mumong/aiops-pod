## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod workload in aiops-case-v08 is stuck in CrashLoopBackOff state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `Warning BackOff 3s (x142 over 30m) kubelet Back-off restarting failed container app in pod workload_aiops-case-v08` | 确认 Pod 在 30 分钟内反复重启，已触发退避机制 |
| 2 | K8s State | `kubernetes` | `container.app.last_terminated_reason=Error`, `container.app.last_exit_code=127` | 证明容器进程以错误状态退出，错误码 127 典型对应“命令未找到” |
| 3 | Logging | `elasticsearch` | `2026-09-11T13:03:32.103Z`: `sh: exec: line 0: /opt/app/unavailable-command: not found` | 直接提供容器启动失败的具体报错，确认二进制路径不存在 |
| 4 | K8s Config | `kubernetes` | `container.app.resource_request.memory=8Mi`, `container.app.resource_limit.memory=32Mi` | 资源配额极低，排除 OOM（内存不足）导致 CrashLoopBackOff 的可能性 |
| 5 | K8s State | `kubernetes` | `pod.condition[00e5e755-886e-4661-9e8a-00d1e71595f6].Ready=False`, `container.app.waiting_reason=CrashLoopBackOff` | 确认 Pod 当前处于不健康状态，等待原因为 CrashLoopBackOff |

**证据分析：**
Logging 中的具体错误信息 `/opt/app/unavailable-command: not found` 与 K8s State 中的退出码 127 完全吻合，直接锁定了“镜像内文件缺失”这一导致容器启动失败的直接原因。结合 K8s Config 中极低的内存限制（8Mi/32Mi），排除了资源不足引发的异常退出。多组事实相互印证，构建了清晰的故障逻辑链。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了镜像中不存在的二进制文件 /opt/app/unavailable-command → 容器进程启动失败，退出码 127 (命令未找到) → Kubernetes 重启策略触发反复重启 → Pod 进入 CrashLoopBackOff 状态并标记为未就绪
```

### 根因结论

已确认根因：容器应用 `app` 启动配置中指定的入口点 `/opt/app/unavailable-command` 在基础镜像 `xnet.registry.io:8443/observability/python:3-alpine` 中不存在（事实编号：3, 2）。

这导致了容器启动时的“命令未找到”错误，进而引发了持续的 CrashLoopBackOff 状态（事实编号：1, 5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 15.6s
├─ 并发证据采集: 40.8s
│  └─ g1 aiops-case-v08/workload: 40.8s (Evidence 32.4s, RCA 8.2s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
