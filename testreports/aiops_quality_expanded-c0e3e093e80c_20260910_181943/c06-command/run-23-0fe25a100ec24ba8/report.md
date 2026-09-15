## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod workload in namespace aiops-case-v08 is in CrashLoopBackOff state with high restart count. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Logging | elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 确诊启动失败的直接原因：镜像内缺少指定命令 |
| 2 | K8s State | container | 最后终止原因: Error, 退出码: 127 | 确认进程因找不到命令而立即退出 |
| 3 | K8s State | pod | 状态: Running, 容器重启计数: 10 | 观察窗口内的高频重启事实 |
| 4 | K8s Event | kubelet | `Back-off restarting failed container app` (发生 118 次，持续 27 分钟) | 证明 Kubernetes 已尝试多次启动并进入退避循环 |
| 5 | K8s State | container | 等待原因: CrashLoopBackOff | 确认 Pod 处于 CrashLoopBackOff 异常状态 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total` = 10, `kube_pod_container_status_waiting_reason(CrashLoopBackOff)` = 1 | 独立指标数据与 K8s 状态完全一致 |

**证据印证说明**：
日志（#1）直接解释了 K8s 状态（#2）中退出码 127 的成因。K8s 事件（#4）和指标（#5, #6）共同验证了该启动失败并非偶发，而是持续触发了 Kubernetes 的重启退避机制。

## 🎯 根因分析 · g1

### 因果链

```text
容器镜像不包含 /opt/app/unavailable-command 文件 → 启动执行时抛出 "command not found" (Exit 127) → kubelet 检测到进程异常终止并触发指数退避策略 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因是容器启动命令配置错误。

Pod `workload` 的容器 `app` 配置的启动命令 `/opt/app/unavailable-command` 在基础镜像中不存在（日志 `fact-1f26c7f41d44` 明确报错 `not found`，状态 `fact-4f273694ffda` 记录退出码 127）。这导致容器每次启动后立即崩溃，K8s 检测到连续失败后将其状态标记为 `CrashLoopBackOff` 并限制重启频率（事件 `fact-146dbd40a566`、状态 `fact-f0ce9becda06`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 12.9s
├─ 并发证据采集: 41.7s
│  └─ g1 aiops-case-v08/workload: 41.7s (Evidence 31.6s, RCA 10.0s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
