## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod配置了不存在的入口命令/opt/app/unavailable-command，导致容器启动即退出(exit 127)并触发CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container=app, exit_code=127 | 证明容器启动即失败且找不到命令 |
| 2 | Logging | elasticsearch | "sh: exec: line 0: /opt/app/unavailable-command: not found" | 明确指出生效命令的路径与原因 |
| 3 | K8s State | kubernetes | container=app, reason="CrashLoopBackOff", restart_count=8 | 确认处于重试退避阶段 |
| 4 | K8s Event | kubernetes | "Warning BackOff ... Back-off restarting failed container app" | 佐证持续的 CrashLoop 现象 |
| 5 | Metric | prometheus | kube_pod_container_status_restarts_total=8 (container=app) | 独立观测到重启计数，与 K8s 事实一致 |

- 事实 #1 (Exit 127) 与事实 #2 (Logging not found) 在因果链上完全闭环，直接指向配置型错误。
- 事实 #3、#4 和 #5 分别从 K8s 状态、K8s 事件和 Prometheus 指标三个维度独立证实了容器持续重启且进入退避循环的现状。

## 🎯 根因分析 · g1

### 因果链

```text
Pod配置了不存在的入口命令 /opt/app/unavailable-command → 容器启动即失败(exit 127) → 触发 CrashLoopBackOff → 应用持续重启并不可用
```

### 根因结论

已确认的根因为 **应用入口命令配置错误**。Pod 的 `app` 容器被配置了命令 `/opt/app/unavailable-command`，但该文件在容器环境中不存在，导致进程立即以退出码 127 退出 [事实 #1, #2]。K8s 控制器检测到失败后，不断重启容器并进入退避状态（CrashLoopBackOff），导致服务不可用 [事实 #3, #4, #5]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 15.6s
├─ 并发证据采集: 45.7s
│  └─ g1 aiops-case-v08/workload: 45.7s (Evidence 40.6s, RCA 4.9s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime, pod-imagepull-failed
