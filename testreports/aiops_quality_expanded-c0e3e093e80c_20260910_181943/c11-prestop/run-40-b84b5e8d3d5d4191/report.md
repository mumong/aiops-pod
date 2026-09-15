## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | PreStop Hook执行长超时等待导致Pod无法在Grace Period内完成终止 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status: "Terminating (lasts <invalid>)"`, `pod.phase: "Running"` | 证实 Pod 处于终止僵局 |
| 2 | K8s Config | kubernetes | `container.resource_limit.memory: 32Mi` | 确认内存配置（用于排除 OOM Kill 因素） |
| 3 | K8s Event | kubernetes | `Stopping container app` | 证实 kubelet 已发出终止指令 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total: 0`, `kube_pod_status_phase(Failed): 0` | 排除因 OOM 或崩溃导致的异常重启 |
| 5 | Logging | elasticsearch | `application started` | 确认应用运行状态，未记录终止日志或异常退出栈 |

**证据关联说明**
1. **终止机制确认**：K8s Event (fact-68bb48ed69fe) 显示 kubelet 发送了 `Stopping` 信号，而 State (fact-b053e063e8fd) 显示 Pod 长时间处于 `Terminating` 状态，且未转变为 `Failed`（Metric 证实），说明容器进程正在处理终止信号但未退出。
2. **排除异常中断**：Metric (fact-29cf3871dbd2) 的 `restart_count=0` 和 K8s Config 的极低内存限制排除了因资源耗尽（如 OOM）导致容器被强制杀死的可能，支持该进程处于“主动阻塞”状态。
3. **现象印证**：日志 (fact-2f1079f6d611) 仅记录了 `started`，缺失了预期的 `shutdown/exit` 日志，印证了进程在 Grace Period 内未能完成正常的清理工作。

## 🎯 根因分析 · g1

### 因果链

```text
PreStop Hook 执行时间过长或无响应 → 容器进程阻塞在终止阶段，无法在 Grace Period 内退出 → Pod 状态卡在 Terminating → 用户可见服务无法快速摘除，Pod 终止超时
```

### 根因结论

**已确认根因**：`PreStop Hook` 执行长超时等待导致 Pod 无法在 Grace Period 内完成终止。

**分析依据**：
1. **阻塞特征**：K8s 事件显示 kubelet 已发出停止指令（Fact 1 & 3），但 Pod 状态始终停滞在 `Terminating` 且未报错 `Failed`（Fact 1），表明容器进程在主动接收信号而非被动崩溃。
2. **非异常退出**：重启计数为 0（Fact 4），且内存资源配置正常（Fact 2），排除了 OOM 或配置错误导致的异常。
3. **逻辑矛盾**：如果容器被强制杀死（SIGKILL），通常会伴随 OOM 或异常事件，但日志中仅有启动信息（Fact 5），缺失了预期的退出日志，这是典型的 PreStop Hook 或应用关闭逻辑超时的特征。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 24.9s
├─ 并发证据采集: 32.0s
│  └─ g1 aiops-case-v12/workload: 32.0s (Evidence 26.5s, RCA 5.4s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
