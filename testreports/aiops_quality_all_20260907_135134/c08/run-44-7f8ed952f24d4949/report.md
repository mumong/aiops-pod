## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | 容器内存限制配置过低 (64Mi)，无法满足应用处理请求时的内存增长需求，触发 OOM Killer 导致进程被终止。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (fact-917ceff132bf) | terminated_reason: "OOMKilled" | 确定进程被内核 OOM Killer 强制终止的直接原因 |
| 2 | K8s State | kubernetes (fact-7e0683512805) | resource_limit.memory: 64Mi | 暴露容器硬限制配置过低，为内存不足提供量化事实 |
| 3 | K8s Event | kubernetes (fact-af43bdde5502) | message: "Back-off restarting failed container app" (102s, x475) | 验证由于内存耗尽导致的 CrashLoopBackOff 现象及高频重启 |
| 4 | Metric | prometheus (fact-6c8305960307) | last_terminated_reason: "1" (label: reason="OOMKilled") | 独立于 K8s API 确认终止原因一致，排除临时状态异常 |
| 5 | Logging | elasticsearch (fact-192cb65db7bd) | pattern: "memory allocation advanced", allocated_mib: 10 -> 46 | 业务日志直接记录内存持续增长，证实应用存在内存消耗需求，且趋势逼近 64Mi 限制 |

**证据印证关系：**
证据 1、4 共同指向 OOMKilled，确证了非正常退出的内核机制。证据 2 (64Mi 限制) 与证据 5 (日志中内存分配达到 46Mi 且仍在增长) 形成了完整的因果闭环：有限的硬限制无法满足应用持续增长的业务内存需求，最终触发证据 1 的内核干预，导致了证据 3 描述的频繁重启现象。

## 🎯 根因分析 · g1

### 因果链

```text
配置硬限制过低 (64Mi) → 无法满足业务内存增长需求 (日志记录至 46Mi) → 触发 Linux OOM Killer 终止进程 → CrashLoopBackOff 导致容器反复重启
```

### 根因结论

已确认根因为容器内存限制配置过低。
1. **资源瓶颈**：容器 `app` 设置了极低的内存硬限制 `64Mi`（证据 2）。
2. **需求冲突**：应用日志明确记录了内存分配过程，在观测窗口内已从 `10Mi` 增长至 `46Mi`，呈现持续增长趋势且逼近系统限制（证据 5）。
3. **崩溃机制**：当可用内存不足以支撑应用进一步操作时，Linux 内核 OOM Killer 介入，以 exit code 137 终止了容器进程（证据 1, 3）。
4. **现象表现**：Kubernetes 检测到容器异常退出后，按照 CrashLoopBackOff 策略不断尝试重启，导致服务不可用（证据 3, 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 18.9s
├─ 并发证据采集: 59.4s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 59.4s (Evidence 51.5s, RCA 7.8s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
