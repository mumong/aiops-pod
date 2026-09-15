## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | 容器内存请求/限制配置严重不足 (64Mi)，而启动逻辑显式尝试分配 256Mi 内存，导致触发 OOMKilled 并进入 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.resource_limit.memory=64Mi, container.resource_request.memory=8Mi | 确认当前内存资源限制为 64Mi，上限极低 |
| 2 | K8s State | kubernetes | container.last_exit_code=137 | Exit Code 137 为进程被 OOM Killer 强制终止的标准标识 |
| 3 | K8s State | kubernetes | container.last_terminated_reason=OOMKilled, container.waiting_reason=CrashLoopBackOff | 直接反映内核 OOM 触发机制及当前的崩溃循环状态 |
| 4 | K8s Event | kubernetes | reason=OOMKilled, reason=BackOff (3m56s x395 over 88m) | BackOff 事件记录证实了崩溃的反复发生与当前退避状态 |
| 5 | Logging | elasticsearch | log.message=startup allocation 256Mi | 显式证据表明应用启动时试图分配 256Mi 内存，直接突破 64Mi 限制 |
| 6 | Metric | prometheus | kube_pod_container_status_restarts_total=22, reason=OOMKilled | 从监控视角独立证实容器已累计 OOM 重启 22 次 |

**证据综合说明：**
Kubernetes 状态事实（#2, #3）与事件（#4）共同锁定了 `OOMKilled` 这一失败机制。日志（#5）与资源配置（#1）构成了直接的因果矛盾：应用启动时要求 256Mi，而容器限制仅为 64Mi。Metric 数据（#6）从时间序列上印证了该配置缺陷导致了反复的崩溃循环。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置 memory limit 为 64Mi → 容器启动时分配 256Mi 内存 → 内存分配超过限制，触发内核 OOM Killer → 容器被强制终止 (Exit Code 137)，Kubernetes 反复重启失败
```

### 根因结论

已确认的根因为 **容器内存资源限制（64Mi）远低于应用启动时的显式内存分配需求（256Mi）**。

1. **机制确认**：应用进程在启动阶段尝试分配 256Mi 内存，直接突破了容器 64Mi 的 `memory limit`（事实 #1, #5）。
2. **故障表现**：由于内存超限，触发内核 OOM Killer 机制（事实 #2, #3），导致容器以 Exit Code 137 退出并被 Kubernetes 反复重启进入 CrashLoopBackOff 状态（事实 #3, #4, #6）。

当前证据充分证实了配置缺陷与 OOM 崩溃之间的直接因果关系。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 23.8s
├─ 并发证据采集: 45.8s
│  └─ g1 aiops-case-v15/workload: 45.8s (Evidence 37.9s, RCA 7.7s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
