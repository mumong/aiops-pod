## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Pod aiops-case-v15/workload 处于 CrashLoopBackOff 状态，容器 app 反复重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: OOMKilled` (fact-1adb8a66f43b) | 确认容器被内核强制终止的直接原因 |
| 2 | K8s Event | Kubernetes | `BackOff 3m59s (x281 over 63m)` (fact-a4def6106f7a) | 确认因反复重启导致的退避行为 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory: 64Mi` (fact-7c7a215ee9f8) | 确认系统层面的硬限制资源上限 |
| 4 | Logging | Elasticsearch | `startup allocation 256Mi` (fact-05468ba107e7) | 确认应用层实际需要的内存分配量 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason {reason: "OOMKilled"}` (fact-3a4d3eda0ace) | 独立验证了内核级 OOM 终止事实 |
| 6 | K8s State | Kubernetes | `container.last_exit_code: 137` (fact-b2fc01d07c07) | 确认容器因信号 SIGKILL (128+9) 退出 |

**证据印证说明：**
1. **资源限制 vs 实际需求冲突**：配置上限 `64Mi` (fact-3) 明显低于启动所需 `256Mi` (fact-4)。
2. **内核行为确认**：退出码 `137` (fact-6) 与终止原因 `OOMKilled` (fact-1, fact-5) 逻辑一致，确认为 OOM 机制而非应用逻辑错误。
3. **状态连锁反应**：OOMKilled (fact-1) 导致容器重启，进而触发 kubelet 的 `BackOff` 事件 (fact-2) 和 `CrashLoopBackOff` 状态。

## 🎯 根因分析 · g1

### 因果链

```text
memory limit (64Mi) 低于应用启动需求 (256Mi) → OOMKilled (exit code 137) → kubelet 重启触发退避 → CrashLoopBackOff 状态
```

### 根因结论

已确认根因为**容器内存限制设置过小**。
具体证据支撑如下：
1. **资源不足**：工作负载配置了 `64Mi` 的内存硬限制 (fact-3)，但应用日志显示启动分配需要 `256Mi` (fact-4)，资源缺口显著。
2. **机制匹配**：Pod 状态持续显示 `OOMKilled` (fact-1, fact-5) 且伴随退出码 `137` (fact-6)，证明进程因超限制被系统 Kill 掉。
3. **现象关联**：OOM 导致容器崩溃并不可逆重启，进而触发 `BackOff` 逻辑 (fact-2)，最终表现为 `CrashLoopBackOff` (fact-2, fact-a4def6106f7a)。

该结论逻辑闭环完整，Kubernetes 状态、内核事件与应用日志相互印证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 21.3s
├─ 并发证据采集: 49.6s
│  └─ g1 aiops-case-v15/workload: 49.6s (Evidence 40.5s, RCA 8.9s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime, pod-oomkilled
