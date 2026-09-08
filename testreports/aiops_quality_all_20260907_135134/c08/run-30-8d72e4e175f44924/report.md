## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | Container 'app' in Pod 'workload-5c9c7b6489-wmjhr' is stuck in CrashLoopBackOff state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: OOMKilled`, `Exit Code: 137` | 确认应用进程被内核 OOM Killer 强制终止。 |
| 2 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff`, `back-off 5m0s restarting` | 确认由于持续崩溃导致 K8s 重启策略触发指数退避。 |
| 3 | K8s Config | Kubernetes | `resource_limit.memory: 64Mi`, `resource_request.memory: 24Mi` | 确认应用可用的最大硬内存上限仅为 64Mi。 |
| 4 | Metric | Prometheus | `container_memory_working_set_bytes`: 近期多次观测值达 `~51343360` (48.9Mi) 和 `~45113344` (43Mi)，最大峰值 `~66236416` (63.1Mi) | 证实应用运行期间内存持续逼近且超过 64Mi 硬限制。 |
| 5 | Logging | Elasticsearch | `log.message: "memory allocation advanced"`, `numeric_fields: allocated_mib first=12, last=44` (连续 7 次) | 确认业务请求 `/work` 中应用逻辑存在连续的内存分配行为。 |
| 6 | Tracing | Deepflow | `HTTP GET /work`: 响应 `200`, 发生 7 次等效 L7 Flow | 确认触发上述日志中内存增长的业务请求在崩溃前确实被成功处理。 |

**证据逻辑说明：**
Kubernetes 事实（#1, #2）与应用退出码 `137` 结合，明确指向 OOM 崩溃；配置事实（#3）锁定了触发 OOM 的容量阈值（64Mi）；Metric 事实（#4）记录了该 Pod 在运行期间内存不断逼近该阈值的过程，与 K8s 的 OOM 终止状态相互印证；Logging（#5）和 Tracing（#6）进一步锁定了引发内存持续增长的特定业务行为（处理 `/work` 请求时进行大量内存分配）。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理 '/work' 请求执行迭代内存分配 → 内存占用线性增长并逼近/突破容器 64Mi 硬上限 → 触发内核 OOM Killer 终止进程 (Exit 137) → 触发 CrashLoopBackOff 重启循环
```

### 根因结论

已确认根因为：容器 `app` 被配置了极低的内存硬限制（`64Mi`），而应用在处理 `/work` 请求时的业务逻辑导致内存占用发生线性增长。
当应用内存消耗（观测到的峰值约为 `48.9Mi` - `63.1Mi`）触达或超过该 `64Mi` 硬限制时，容器运行时的内存管理机制触发内核 OOM Killer 强制杀死进程。Kubernetes 随后尝试重启该容器，但由于内存泄漏/增长模式重复出现并持续触发 OOM，最终导致 Pod 陷入 `CrashLoopBackOff` 状态。证据链涵盖了从应用日志中的内存分配意图（Logging #5）、实际内存消耗数据（Metric #4）到内核终止信号（K8s State #1）的完整闭环。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 12.2s
├─ 并发证据采集: 104.3s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 104.3s (Evidence 90.5s, RCA 13.6s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
