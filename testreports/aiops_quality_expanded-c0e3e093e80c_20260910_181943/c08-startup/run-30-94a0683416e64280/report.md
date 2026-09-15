## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Container memory limit (64Mi) is significantly lower than application startup allocation (256Mi), causing OOMKilled (Exit Code 137) and subsequent CrashLoopBackOff. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.last_terminated_reason: `OOMKilled` (fact-0785b884910b) | 直接证明进程因内存耗尽被系统杀死 |
| 2 | K8s State | Kubernetes | container.last_exit_code: `137` (fact-4376421df468) | 确认退出代码 137 与 OOMKilled 一致 |
| 3 | K8s Config | Kubernetes | container.resource_limit.memory: `64Mi` (fact-9f0e33886869) | 提供容器硬限制值，是导致异常的物理约束 |
| 4 | Logging | Elasticsearch | log.message: `startup allocation 256Mi` (fact-016ce27a1965) | 指出应用启动所需内存为 256Mi，与 64Mi 限制形成直接冲突 |
| 5 | Metric | Prometheus | kube_pod_container_status_last_terminated_reason: `1` (labels: reason=OOMKilled) (fact-9a9b09cf3ed6) | 独立验证了终止原因的客观事实 |
| 6 | Metric | Prometheus | kube_pod_container_status_waiting_reason: `1` (labels: reason=CrashLoopBackOff) (fact-b13d407243ba) | 确认容器当前处于重启退避等待状态 |
| 7 | K8s Event | Kubernetes | BackOff restarting failed container (x395 over 85m) (fact-041bda937357) | 确认异常持续时间长，符合配置错误导致的循环崩溃 |

Kubernetes 层面记录的状态、退出码和事件证实了进程被 OOMKilled 并进入 CrashLoopBackOff；Metric 维度独立观测到相同的 OOMKilled 状态和 CrashLoopBackOff 等待原因；Logging 维度记录了 256Mi 的启动分配需求，解释了为何 64Mi 的内存限制必然导致进程被杀。三者互证，指向内存配置失衡。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制 (64Mi) 低于应用启动需求 (256Mi) → 启动时触发 OOMKilled → 进程退出并立即重启 → 进入 CrashLoopBackOff 循环
```

### 根因结论

已确认的根因是：容器内存硬限制（`64Mi`，事实 #3）严重低于应用启动时的内存分配需求（`256Mi`，事实 #4）。当容器启动时，应用请求的内存超过了系统硬限制，触发内核 OOM Killer 终止进程，返回退出代码 `137`（事实 #2）。Kubernetes 随后尝试重启容器，但由于配置未变，导致循环崩溃，最终进入 `CrashLoopBackOff` 状态（事实 #5, #6, #7）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 11.2s
├─ 并发证据采集: 39.1s
│  └─ g1 aiops-case-v15/workload: 39.1s (Evidence 32.3s, RCA 6.7s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
