## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Application memory allocation (256Mi) exceeds the configured resource limit (64Mi), triggering OOMKilled. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.last_terminated_reason: OOMKilled (fact-2610900ad89c) | 核心归因：容器因内存超限被内核杀 |
| 2 | K8s Config | kubernetes | container.resource_limit.memory: 64Mi (fact-c1cbfc461ce1) | 核心约束：内存硬性上限 |
| 3 | Logging | elasticsearch | "startup allocation 256Mi" (fact-0e0f3b5f125d) | 直接证据：应用启动申请 256Mi，远超 64Mi 限制 |
| 4 | K8s Event | kubernetes | Warning BackOff (x140 over 33m) (fact-dcacb464cc0a) | 故障现象：重启频繁且已进入指数退避阶段 |
| 5 | K8s State | kubernetes | container.last_exit_code: 137 (fact-14049c327f6c) | 系统反馈：退出码 137 确认 OOM 机制 |

证据之间形成闭环：日志（#3）显示应用试图分配 256Mi 内存，该数值远超配置中的 64Mi 硬限制（#2）。操作系统 OOM Killer 介入终止容器并返回退出码 137（#5），最终导致 Kubernetes 将其标记为 CrashLoopBackOff（#4）。

## 🎯 根因分析 · g1

### 因果链

```text
Resource limit (64Mi) < Allocation needed (256Mi) → OOM Killer Termination (Exit Code 137) → Container Restart Failure → CrashLoopBackOff
```

### 根因结论

已确认的根因是容器内存资源限制配置过低，导致应用启动时申请 256Mi 内存被系统 OOM Killer 强制终止。
- **配置事实**：内存限制被硬限制为 64Mi（#2）；
- **日志事实**：应用启动日志明确记录分配 256Mi（#3）；
- **状态事实**：退出码 137 和终止原因为 OOMKilled（#1, #5）。
上述证据链完整且无冲突。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 18.8s
├─ 并发证据采集: 68.5s
│  └─ g1 aiops-case-v15/workload: 68.5s (Evidence 61.2s, RCA 7.2s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime, pod-oomkilled, pod-config-error, pod-sandbox-create-failed
