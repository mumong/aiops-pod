## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Container memory limit (64Mi) is insufficient for the application startup requirement (256Mi), causing OOMKilled (Exit Code 137) and subsequent CrashLoopBackOff. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | Kubernetes | `container.resource_limit.memory` (app): `64Mi` | 确认受限资源上限 |
| 2 | Logging | Elasticsearch | `startup allocation 256Mi` (2026-09-14T11:14:55Z) | 确认应用启动内存需求 |
| 3 | K8s State | Kubernetes | `container.last_terminated_reason`: `OOMKilled`<br>`container.last_exit_code`: `137` | 确认内存耗尽导致进程被强制杀死的直接机制 |
| 4 | K8s State | Kubernetes | `container.restart_count`: `27` | 确认因 OOMKilled 导致的频繁重启循环 |
| 5 | K8s Event | Kubernetes | `Warning BackOff 57s (x535 over 116m)` | 确认 kubelet 的指数退避重启策略导致 BackOff 异常状态 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason: `CrashLoopBackOff`): `1`<br>`kube_pod_container_status_last_terminated_reason` (reason: `OOMKilled`): `1` | 辅助确认当前的等待状态和上次终止原因 |

**证据关联说明：**
- **事实 1 & 2 证实矛盾**：K8s 配置的硬限制（64Mi）远低于应用日志声明的启动分配需求（256Mi），这是导致 OOMKilled 的必然前提。
- **事实 3 & 5 形成闭环**：OOMKilled (事实 3) 解释了为何会出现 BackOff 事件 (事实 5)，而 BackOff 解释了 Pod 处于 CrashLoopBackOff 状态的原因。
- **事实 4 提供持续性证据**：27 次重启记录了该问题发生的频次，证实为持续性配置缺陷而非单次异常。

## 🎯 根因分析 · g1

```text
资源配置不足 (限制 64Mi < 需求 256Mi) → OOMKilled (Exit 137) → 重启循环 → 异常状态 CrashLoopBackOff
```

### 根因结论

**已确认的根因**：工作负载 `aiops-case-v15/workload` 中的容器 `app` 内存限制配置过低（64Mi），无法满足应用启动时所需的内存（256Mi）。

**因果解释**：
应用启动时申请 256Mi 内存（见 **事实 2**），但因被 K8s 强制限制在 64Mi 以内（见 **事实 1**），导致进程触发 OOM Killer 被终止，退出码为 137（见 **事实 3**）。容器退出后，K8s 自动重启该容器，随即再次因内存不足被杀，最终触发 kubelet 的 BackOff 策略并进入 CrashLoopBackOff 状态（见 **事实 4, 5**）。上述逻辑已被 Kubernetes 状态、Event 事件、Prometheus 指标及应用日志完整印证（见 **证据内容** 中的 1-6）。

---

## 📊 性能统计

```text
├─ 总耗时: 9.3m
├─ 问题定位: 12.6s
├─ 并发证据采集: 533.0s
│  └─ g1 aiops-case-v15/workload: 533.0s (Evidence 528.3s, RCA 4.5s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime, pod-oomkilled
