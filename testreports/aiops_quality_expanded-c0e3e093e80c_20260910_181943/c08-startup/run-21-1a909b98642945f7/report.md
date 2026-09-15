## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Pod workload (aiops-case-v15)处于 CrashLoopBackOff 状态，容器反复重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Event | `kubelet` 发出 `Warning BackOff`：`back-off 5m0s restarting failed container=app pod=workload_aiops-case-v15` (事实ID: fact-23f5b043f4ac, fact-65d5bd6ff646) | 证明容器处于 CrashLoopBackOff 循环重启状态 |
| 2 | K8s State | K8s State | 容器最终终止原因为 `OOMKilled` (事实ID: fact-733022f59511)；退出码 `137` (事实ID: fact-32795fbf8e7e, fact-04ca4ae59c51) | 确认进程是被内核 OOM Killer 强制杀死的直接原因 |
| 3 | K8s Config | K8s Config | 容器内存硬限制 (limit) `64Mi` (事实ID: fact-35d2857835fb) | 提供触发 OOM 的资源阈值依据 |
| 4 | Logging | Logging | 容器启动日志显示 `startup allocation 256Mi` (事实ID: fact-5666220a64f9) | 证明容器实际尝试分配 (256Mi) 远超其硬限制 (64Mi)，构成内存超限行为 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` 标签 `reason=OOMKilled` (事实ID: fact-b242b245ae1e) | 独立确认容器上次非正常退出的原因 |
| 6 | K8s State | K8s Event | Pod `ContainersReady` 和 `Ready` 状态为 `False` (事实ID: fact-0eaeb56433d2, fact-f23daedea971) | 展示故障导致 Pod 服务不可用的直接结果 |

**证据逻辑：**
*   **直接触发机制**：K8s 配置事实 #3 显示容器仅有 64Mi 内存限制，而日志事实 #4 显示启动时强占 256Mi，直接违反了限制。
*   **内核响应与现象**：内核 OOM Killer 介入，导致容器以退出码 137 被杀（事实 #2）；K8s 层面记录终止原因 `OOMKilled`（事实 #2, #5），并进入 CrashLoopBackOff 退避状态（事实 #1）。

## 🎯 根因分析 · g1

### 因果链

```text
容器启动命令强制分配 256Mi 内存 (logging fact-5666220a64f9) 
  → 超过 K8s 硬限制 64Mi (K8s config fact-35d2857835fb) 
  → 触发 Linux OOM Killer 终止进程 (signal 9) 
  → 容器非正常退出 (exit code 137, fact-32795fbf8e7e, fact-733022f59511) 
  → Kubelet 触发 CrashLoopBackOff 退避重启 (event fact-65d5bd6ff646)
```

### 根因结论

已确认的根因为：**容器启动时尝试分配的内存资源 (256Mi) 严重超出 K8s 设定的内存硬限制 (64Mi)，导致 Linux 内核 OOM Killer 强制终止容器进程。**

支持证据包括：日志中明确记录了容器启动时的内存分配行为（事实 #4）；K8s 配置状态证明了严格的资源上限（事实 #3）；并且 K8s State、Metric、日志三者均一致证实了由内存超限引发的 OOMKilled 事件（事实 #2, #5, #1）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 16.7s
├─ 并发证据采集: 54.9s
│  └─ g1 aiops-case-v15/workload: 54.9s (Evidence 45.3s, RCA 9.4s)
└─ 汇总总结: 13.3s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
