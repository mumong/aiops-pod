## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | Running | Pod aiops-case-08/workload-5c9c7b6489-fl85h 处于 CrashLoopBackOff 状态，容器因内存耗尽被系统强制杀死 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s | Container `app` exit code `137`，`last_terminated_reason` 为 `OOMKilled`，`waiting_reason` 为 `CrashLoopBackOff` | 明确终止原因为系统强制杀进程，直接指向 OOM |
| 2 | K8s Config | K8s | Container `app` `resource_limit.memory` 配置为 `64Mi` | 提供判定内存不足的上限基准 |
| 3 | Metric | Prometheus | `container_memory_usage_bytes` 在采样周期内出现 `38MB`、`55MB`、`61MB` 峰值（Max 61743104 Bytes ≈ 58.9 MiB） | 证明应用内存实际使用量逼近并触及 64Mi 限制 |
| 4 | Logging | Elasticsearch | 日志 pattern `memory allocation advanced` 在 `15:32:52` 至 `15:33:20` 期间连续触发，`allocated_mib` 从 `12` 激增至 `40` | 展示应用侧内存增长的动态过程，为 OOM 提供行为证据 |

证据表明，应用在运行期间持续分配内存（日志显示从 12MB 增长至 40MB），导致其内存使用量（指标最高达 ~58.9MB）逼近 64Mi 的硬限制，最终触发 Linux OOM Killer 终止进程（退出码 137），并导致 Kubelet 反复重启失败进入 CrashLoopBackOff。

## 🎯 根因分析 · g1

### 因果链

```text
应用工作负载持续增长内存分配 (最大峰值 > 58.9 MiB) → 内存使用量突破资源限制上限 (memory limit: 64Mi) → Linux OOM Killer 强制终止容器进程 (exitCode: 137) → Kubelet 检测容器退出并触发重启策略，导致 CrashLoopBackOff
```

### 根因结论

已确认根因为容器内存限制配置过低（64Mi），无法承载应用在该窗口内的内存增长模式（实测峰值达 ~58.9 MiB），触发 Linux OOM Killer 终止进程，进而引发 Kubelet 反复重启导致的 CrashLoopBackOff。该结论由 K8s 状态（OOMKilled、Exit 137）、Metric 数据（使用量逼近限制）及 Logging 数据（分配量持续增长）相互印证。

---

## 📊 性能统计

```text
├─ 总耗时: 2.9m
├─ 问题定位: 26.9s
├─ 并发证据采集: 138.6s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 138.6s (Evidence 127.3s, RCA 11.0s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-oomkilled, pod-crashloop-runtime
