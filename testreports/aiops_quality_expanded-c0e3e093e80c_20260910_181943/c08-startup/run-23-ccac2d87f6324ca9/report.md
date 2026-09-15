## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | 容器启动时尝试分配256Mi内存，超过`limits.memory`设定的64Mi硬限制，触发OOMKilled，导致进程以退出码137终止并进入CrashLoopBackOff循环。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: {"container": "app", "reason": "OOMKilled"} (fact-51f480238127) | 确认容器被系统强制终止，直接归因为内存超限 |
| 2 | K8s Config | kubernetes | `container.resource_limit.memory`: 64Mi (fact-27f0963a198a) | 提供故障判定基准，确认为 64Mi 硬限制 |
| 3 | Logging | elasticsearch | `log.message`: "startup allocation 256Mi" (fact-5666220a64f9) | 记录进程启动阶段的实际内存请求，证实超过上限 |
| 4 | K8s Event | kubernetes | `BackOff restarting failed container app` (fact-9fe998cbdc4d) | 展现因 OOM 导致的崩溃循环现象 |

证据间互相印证：Logging 指出应用试图申请 256Mi，K8s Config 确认硬限制仅为 64Mi，K8s State 与 K8s Event 记录证实该超额尝试直接触发了 `OOMKilled` (fact-51f480238127) 及后续的 `CrashLoopBackOff` 重启循环 (fact-945356d308c6)。

## 🎯 根因分析 · g1

### 因果链

```text
容器配置硬限制为64Mi → 进程启动时尝试申请256Mi内存 → 触发OOMKilled强制终止(退出码137) → 进入CrashLoopBackOff循环
```

### 根因结论

已确认根因为 **内存资源配置冲突（Request > Limit）**。

根据事实支撑：
1. **K8s 状态**明确显示容器被 `OOMKilled` (fact-51f480238127)，证明进程在启动初期即触发了系统的 OOM Killer。
2. **配置事实**记录了 `limits.memory` 仅为 `64Mi` (fact-27f0963a198a)。
3. **日志事实**记录 `startup allocation 256Mi` (fact-5666220a64f9)，证实应用启动时的内存需求远超硬限制。

上述三组事实构成完整证据链，确证根因为容器启动时所需内存（256Mi）显著超出其 `limits.memory` 硬限制（64Mi），导致无法分配内存而被系统杀死并循环重启。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 38.9s
├─ 并发证据采集: 71.7s
│  └─ g1 aiops-case-v15/workload: 71.7s (Evidence 65.5s, RCA 6.0s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime, pod-oomkilled
