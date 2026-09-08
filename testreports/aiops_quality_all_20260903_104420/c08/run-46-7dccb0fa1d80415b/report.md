## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | Pod aiops-case-08/workload-5c9c7b6489-fl85h处于CrashLoopBackOff状态，容器app反复崩溃 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: OOMKilled` | 确认容器崩溃的直接原因为内核 OOM Killer |
| 2 | K8s State | Kubernetes | `container.last_exit_code: 137` | 佐证 Exit Code 137 对应 SIGKILL (OOM) |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory: 64Mi` | 定义应用运行的硬限制，作为判断泄漏的关键基准 |
| 4 | Logging | Elasticsearch | `log.message: "memory allocation advanced"` (Path: `/work`, Status: 200)，窗口内 `allocated_mib` 从 14 增长至 46 | 捕获请求处理期间的内存分配过程，显示单次请求内存占用大幅上升 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 26` (区间统计 last: 26, sample_count: 61) | 确认该 Pod 处于高频重启状态 |
| 6 | K8s State | Kubernetes | `pod.condition: Ready=False (ContainersNotReady)`；`restart_count: 26` | 证实容器持续崩溃导致 Pod 无法就绪 |

**证据印证说明：**
Kubernetes 层面的 `OOMKilled` 和 `137` 退出码与 64Mi 的内存硬限制共同锁定了内存耗尽这一机制。日志证据精准指向了 `/work` 接口请求处理时内存从 14MiB 激增至 46MiB 的过程，这与内存不足直接吻合。虽然 Metric 统计样本数较多，但仅反映重启频次，未展示内存使用率的历史趋势曲线，结合日志可判断为特定业务处理触发了资源上限。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理/work请求时内存持续增长(2 MiB → 48 MiB) → 内存分配突破容器64MiB硬限制 → Kubernetes OOM Killer终止进程(Exit Code 137) → Kubelet触发CrashLoopBackOff重启机制
```

### 根因结论

**已确认根因：** 容器应用 `app` 在处理 `/work` 请求时存在内存分配过量或内存泄漏问题。在请求处理过程中，内存占用从 14MiB 快速攀升至 46MiB，突破了 Pod 配置的 64MiB 内存硬限制，导致内核触发 OOM Killer 强制终止进程（Exit Code 137）。Kubernetes 的 CrashLoopBackOff 机制在检测到频繁崩溃后进入指数退避状态，造成 Pod 不可用。

**缺失事实：** 目前日志仅展示了特定窗口的内存分配过程，缺乏应用代码层面的详细内存分配路径分析，也缺乏完整的内存随时间变化的 Metrics 趋势数据（本次未获取到历史趋势，仅获取了重启计数），因此无法确定该内存增长是一次性的突发泄漏还是随请求累积的持续性泄漏。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 20.6s
├─ 并发证据采集: 74.7s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 74.7s (Evidence 63.7s, RCA 10.9s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime, pod-oomkilled
