## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `reason: OOMKilled` (fact-0696ea453721) | 确认容器因超出资源上限被内核强制终止 |
| 2 | K8s Config | kubernetes | `resource_limit.memory: 64Mi` (fact-220a641b6dec) | 提供判定 OOM 的硬阈值依据 |
| 3 | K8s Event | kubernetes | `Exit Code: 137` 及 `Back-off restarting failed container app` (fact-f9e1754a32fc, fact-192dd219139f) | 佐证容器异常退出及随后的重启循环机制 |
| 4 | Metric | prometheus | `container_memory_working_set_bytes` 峰值达 `63856640` Bytes (约 60.9Mi)，发生于 16:23 (fact-63105fc574b9) | 证明应用实际内存消耗极度逼近 64Mi 限制，触发 OOM 的直接前置条件 |
| 5 | Logging | elasticsearch | `allocated_mib` 在请求处理窗口内从 `10` 激增至 `48` (fact-3bd4fdc80c2b) | 刻画应用内存增长的速率与幅度，表明存在突发或累积性的内存分配行为 |

**证据关联说明：**
K8s 指标 (fact-63105fc574b9) 记录到内存峰值约为 60.9Mi，非常接近配置的上限 64Mi (fact-220a641b6dec)，这与日志 (fact-3bd4fdc80c2b) 显示的请求内内存分配量达到 48Mi 的峰值高度吻合。结合内核返回的 `OOMKilled` (fact-0696ea453721) 和退出码 `137` (fact-f9e1754a32fc)，逻辑闭环确认了内存超限是终止容器的唯一原因。

## 🎯 根因分析 · g1

### 因果链

```text
应用每次请求处理中内存分配增长 (10Mi -> 48Mi) → 内存峰值触及 64Mi 容器限制硬上限 → 触发 OOMKilled (Exit Code 137) → 容器持续崩溃重启导致 CrashLoopBackOff
```

### 根因结论

根因已确认为 **`Container memory limit (64Mi) is insufficient for the application's memory growth pattern`**。

证据链 (事实 1, 2, 4, 5) 表明，应用在处理请求时会出现显著的内存增长，其峰值消耗 (约 60.9Mi) 极其逼近当前设定的容器内存硬限制 (64Mi)。由于缺乏内存缓冲空间，容器达到了 OOM Kill 阈值，导致进程被 Linux OOM Killer 终止。

---

## 📊 性能统计

```text
├─ 总耗时: 3.0m
├─ 问题定位: 15.1s
├─ 并发证据采集: 151.8s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 151.8s (Evidence 141.6s, RCA 10.0s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime, pod-oomkilled
