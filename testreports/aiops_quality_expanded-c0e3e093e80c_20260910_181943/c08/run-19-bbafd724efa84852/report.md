## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | Pod aiops-case-08/workload-5c9c7b6489-p8462 处于 CrashLoopBackOff 状态，无法就绪。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: OOMKilled, `container.last_exit_code`: 137 | 确认进程因内存不足被系统强制终止。 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff | 确认 Pod 处于重启失败、进入退避循环的状态。 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory`: 64Mi | 确认容器内存硬限制为 64Mi，为根因提供定量基准。 |
| 4 | K8s Event | kubernetes | `event.message`: BackOff restarting failed container app... | 证实系统正在执行高频率的重启操作。 |
| 5 | Logging | elasticsearch | 日志模式: `memory allocation advanced`, `allocated_mib` 从 10 跃升至 48 | 展现应用运行过程中内存占用的持续增长趋势，逼近并突破限制。 |
| 6 | Tracing | deepflow | HTTP GET /work 响应码 200, 耗时 6324us - 24960us | 确认该内存增长发生在正常的业务请求处理过程中。 |

**证据印证说明：**
1. **异常现象闭环**：证据 1 和 2 结合表明，应用进程反复崩溃（OOMKilled）并重启，最终触发系统的保护性退避机制（CrashLoopBackOff）。
2. **内存压力因果**：证据 5 显示应用在处理请求时存在明显的内存分配增长，结合证据 3 极低的内存硬限制（64Mi），直接印证了资源配额无法满足运行时需求的结论。
3. **系统行为一致性**：证据 4 的重启频率与证据 5 中短时间内多次内存增长的观察窗口一致，共同指向资源不足导致的持续故障循环。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理请求内存分配突破 64Mi 硬限制 → Linux OOM Killer 强制终止进程 (Exit 137) → 容器重启失败进入 CrashLoopBackOff → Pod 持续处于 CrashLoopBackOff 状态且不可就绪
```

### 根因结论

已确认的根因是：**容器 'app' 运行时的内存分配超出了其配置的 `resource_limit`（64Mi），导致被操作系统 OOM Killer 终止。**

- **事实支撑**：Kubernetes 状态明确报告容器因 `OOMKilled` 终止（证据 1），且退出码为 137（证据 1）。
- **机制印证**：日志记录到应用在处理请求时 `allocated_mib` 从 10 增长到 48（证据 5），显示运行内存消耗快速上升；结合极低的内存限制（证据 3），说明应用内存增长超过了安全水位。
- **现象确认**：由于每次重启后内存继续增长并再次触发 OOM，Kubernetes 判定重启频率过高，将 Pod 置为 `CrashLoopBackOff`（证据 2, 4），阻止了业务恢复。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 20.3s
├─ 并发证据采集: 59.5s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 59.5s (Evidence 49.0s, RCA 10.4s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
