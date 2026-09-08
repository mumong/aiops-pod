## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | 容器内存限制（64Mi）严重不足，导致应用进程因内存超限被内核 OOM Killer 强制终止（Exit Code 137），引发 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.app.last_terminated_reason: `OOMKilled` | 核心诊断：进程因内存超限被内核强制终止 |
| 2 | K8s Config | kubernetes | container.app.resource_limit.memory: `64Mi` | 根因验证：提供导致 OOM 的硬性内存上限阈值 |
| 3 | K8s State | kubernetes | container.app.last_exit_code: `137` | 症状佐证：137 退出码确认进程被信号杀死（非应用自身逻辑退出） |
| 4 | K8s Event | kubernetes | event.message: `Back-off restarting failed container app` | 现象确认：Pod 处于频繁重启恢复的故障循环中 |
| 5 | Metric | prometheus | kube_pod_container_status_last_terminated_reason: `1` (reason: OOMKilled) | 独立观测：Metrics 系统确认最近一次终止原因为 OOM |
| 6 | Logging | elasticsearch | 模式 `memory allocation advanced`: `allocated_mib` 在 17:08:17 - 17:08:55 窗口内从 `10` 增长至 `48` | 机制限定：证明异常发生前应用内存占用持续攀升并逼近 64Mi 限制 |
| 7 | Tracing | deepflow+tempo | HTTP Flow `GET /work`: 状态 `200`，Trace ID `6dcdc9de04eb1da93d34a541a11b7ada` | 关联限定：确认导致内存增长的 `/work` 请求链路在崩溃前被正常执行（响应 200） |

**证据印证说明：**
1. 维度 1、5 从 K8s 状态与 Metrics 两个独立维度确认了“最近一次终止原因为 OOMKilled”。
2. 维度 6 记录了崩溃前的内存持续增长现象（10Mi -> 48Mi），与维度 2 中设置的 64Mi 硬限制高度吻合，解释了触发 OOM Killer 的内存增长机制。
3. 维度 7 提供了完整的关联请求 ID，将日志中记录的内存分配模式与真实的异常请求链路（GET /work）绑定，确认了触发 OOM 的具体请求路径。

## 🎯 根因分析 · g1

### 因果链

```text
容器配置内存硬限制过低（64Mi） → 应用处理请求时内存持续增长并逼近限制（48Mi/49Mi） → 触发内核 OOM Killer 强制终止进程（Exit Code 137 / OOMKilled） → 容器反复重启形成 CrashLoopBackOff
```

### 根因结论

已确认的根因为**容器内存资源限制（64Mi）配置过低**，无法满足应用处理请求时的内存需求。

该配置不足导致应用进程在处理请求（如 GET /work）时，内存分配不断攀升。当内存占用逼近并突破 64Mi 限制时，触发内核 OOM Killer 机制将进程强制终止（退出码 137），进而引发 Pod 反复重启的 CrashLoopBackOff 现象。证据链完整：K8s State/Metrics 确认 OOMKilled 状态，Logs 确认内存增长趋势，Tracing 确认了引发该资源增长的关联请求链路。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 26.0s
├─ 并发证据采集: 54.7s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 54.7s (Evidence 47.9s, RCA 6.6s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
