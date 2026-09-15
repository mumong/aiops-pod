## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | 容器启动命令申请的内存 (256Mi) 超过 Kubernetes 配置的 memory limit (64Mi)，导致 cgroup OOM Killer 强制终止进程 (Exit 137/OOMKilled)。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | `container.resource_limit.memory` | 64Mi | 确认容器内存硬限制 |
| 2 | Logging | `startup allocation` | 256Mi | 确认启动指令实际申请内存 |
| 3 | K8s State | `container.last_terminated_reason` | OOMKilled | 直接触发机制确认 |
| 4 | K8s State | `container.last_exit_code` | 137 | 确认进程被内核强制终止 |
| 5 | K8s State | `container.waiting_reason` | CrashLoopBackOff | 确认最终异常表现 |
| 6 | K8s Event | `kubelet BackOff` | Back-off restarting failed container app in pod workload_aiops-case-v15 (da351bf0-c4ab-47a0-b24d-7c7a75950753) | 描述系统级重启行为 |
| 7 | Metric | `kube_pod_container_status_last_terminated_reason` | 1 (reason: OOMKilled) | 从监控层侧面验证终止原因 |

**证据说明：**
日志与配置对比（事实 #1、#2）明确显示 64Mi 的内存上限无法满足 256Mi 的启动需求，这是触发故障的根本矛盾。K8s 状态事件（事实 #3、#4）与监控数据（事实 #7）共同印证了内核 OOM Killer 介入并发送 SIGKILL 导致容器终止。最终表现为 Kubernetes 控制器触发的指数退避重启循环（事实 #5、#6）。

## 🎯 根因分析 · g1

### 因果链

```text
资源定义限制 (memory limit: 64Mi) 与 启动命令需求 (256Mi) 不匹配 → 进程启动分配 256Mi 内存触发 cgroup 硬限制 → 内核 OOM Killer 发送 SIGKILL 终止容器进程 (Exit Code: 137) → Pod 持续重启陷入 CrashLoopBackOff 状态
```

### 根因结论

**已确认的根因：容器资源限制（64Mi）不足，导致内存溢出被终止（OOMKilled）。**

Kubernetes 配置的 `memory limit` 为 `64Mi`（事实 #1），而日志明确记录启动命令申请内存高达 `256Mi`（事实 #2）。这导致容器启动瞬间触及 cgroup 内存硬限制，触发内核 OOM Killer 强制终止进程，返回 Exit Code 137（事实 #4）。Pod 状态随之进入 `CrashLoopBackOff`（事实 #5、#6），且 Metric 确认最近一次终止原因为 `OOMKilled`（事实 #7）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.9s
├─ 并发证据采集: 44.5s
│  └─ g1 aiops-case-v15/workload: 44.5s (Evidence 38.0s, RCA 6.3s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
