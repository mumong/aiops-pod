## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: OOMKilled (fact-036f0fa761ff) | 确认容器被内核 OOM Killer 终止 |
| 2 | K8s State | Kubernetes | `container.resource_limit.memory`: 64Mi (fact-784540cbb8ff) | 提供内存硬限制边界，结合 OOMKilled 指向资源不足 |
| 3 | Logging | Elasticsearch | `/work` 路径 8 次重复分配记录，内存从 12 MiB 增至 42 MiB (fact-10f0d291496c) | 展示应用内存随请求增长的行为，与 64Mi 限制存在空间冲突 |
| 4 | Tracing | Deepflow | GET /work 9 次成功 (200)，耗时 12131-21064 µs (fact-424444c1e52c) | 确认异常发生在正常的业务请求处理期间，而非网络或入口故障 |
| 5 | K8s Event | Kubernetes | BackOff 事件：back-off 5m0s restarting failed container=app (fact-bcef70d7c410) | 确认重启间隔因连续崩溃而拉长，符合 CrashLoopBackOff 特征 |

**证据分析：**
Kubernetes 状态与日志证据高度一致。K8s 提供了直接的 OOMKilled 终止原因及 64Mi 的硬性限制边界 [1, 2]；日志证据 [3] 进一步证实了应用在处理 `/work` 请求时发生了显著的内存分配（从 12MiB 攀升至 42MiB），这一趋势表明随着处理逻辑的推进，应用极易突破 64MiB 的限制。Tracing 和 K8s 事件数据 [4, 5] 从侧面确认了这是在正常业务负载下触发的连续崩溃与重启循环。

## 🎯 根因分析 · g1

### 因果链
```text
Pod memory limit (64Mi) is insufficient → /work 请求触发内存分配增长 → Kernel OOM Killer (exit code 137) 终止容器进程 → Kubelet 连续重启导致 CrashLoopBackOff
```

### 根因结论
已确认根因为 **容器内存限制（64Mi）过低，无法满足应用运行时的内存增长需求**。

该资源配置限制直接触发了 Linux 内核的 OOM Killer 机制（证据 [1]，状态码 137）。应用在处理 `/work` 端点时，内存占用呈现增长趋势（证据 [3]，12MiB → 42MiB），逼近并突破了 64MiB 的硬性限制（证据 [2]）。这种“运行-超内存-被杀-重启”的循环导致了持续的 CrashLoopBackOff 现象（证据 [5]）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 18.0s
├─ 并发证据采集: 54.6s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 54.6s (Evidence 45.2s, RCA 9.3s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
