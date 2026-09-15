## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Pod aiops-case-v15/workload 处于 CrashLoopBackOff，容器反复重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff ... Back-off restarting failed container app in pod workload_aiops-case-v15` (fact-099c291361f8) | 确认容器因失败而反复重启，直接呈现 CrashLoopBackOff 现象 |
| 2 | K8s State | Kubernetes | Container `app` terminated with reason: `OOMKilled` (fact-017c8579083b) | 确认容器终止的直接机制是 OOM 杀手介入 |
| 3 | K8s State | Kubernetes | Container `app` exit_code: `137` (fact-6fe0c0060673) | Exit Code 137 进一步印证进程是被信号 9 (SIGKILL) 强制终止的 OOM |
| 4 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` = 1 for `OOMKilled` (fact-32165e523e1e) | 独立监控指标确认容器最近一次终止原因为 OOMKilled |
| 5 | Logging | Elasticsearch | `startup allocation 256Mi` (fact-43abbd48fc32) | 揭示应用启动阶段申请了大量内存，是触发 OOM 的具体操作行为 |
| 6 | K8s Config | Kubernetes | Container `app` resource_limit.memory = `64Mi` (fact-1360d2914ecc) | 提供资源硬性限制事实，与日志中的 256Mi 申请值形成矛盾 |

**证据关联说明：**
Kubernetes 的 OOMKilled 终止状态与 Metrics 的 OOMKilled 指标互相印证了容器死亡的直接原因。日志显示应用启动时分配 256Mi 内存，而 K8s 配置的硬性限制仅为 64Mi，这构成了因果链的核心证据，解释了为何 OOM 会发生。Exit Code 137 则是这一过程在系统层面的标准退出码。

## 🎯 根因分析 · g1

### 因果链

```text
资源配置不当(memory limit=64Mi) → 启动申请超限(256Mi) → 触发内核OOM Killer → Exit Code 137 & OOMKilled → 容器重启失败形成 CrashLoopBackOff
```

### 根因结论

已确认的根因是 Pod 资源配置与应用启动需求严重不匹配。
1. 容器被配置了极低的内存硬限制 `64Mi` (fact-1360d2914ecc)。
2. 应用启动时尝试分配 `256Mi` 内存 (fact-43abbd48fc32)。
3. 这一操作超出了内核允许的限制，直接导致 OOM Killer 杀死进程 (fact-017c8579083b, fact-32165e523e1e, fact-43abbd48fc32)。
4. 进程的反复终止和 Kubelet 的重试策略导致 Pod 进入 CrashLoopBackOff 状态 (fact-04ca9ffd52c7, fact-099c291361f8)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 15.8s
├─ 并发证据采集: 47.5s
│  └─ g1 aiops-case-v15/workload: 47.5s (Evidence 39.0s, RCA 8.2s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
