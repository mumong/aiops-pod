## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | Pod workload-5c9c7b6489-wmjhr in CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: "OOMKilled" (`fact-21f1b06d6c98`) | 明确终止原因为系统级 OOM 拦截 |
| 2 | K8s Event | Kubernetes | `event.message`: "Back-off restarting failed container app" (`fact-67185c94ad69`) | 确认因反复退出触发了指数退避重启 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory`: 64Mi (`fact-4e0179ac42cc`) | 提供判定内存溢出的硬限制阈值 |
| 4 | Metric | Prometheus | `container_memory_working_set_bytes` (app): 从 21.7Mi 攀升至 61.9Mi (`fact-a1e739ee8dbf`) | 证实应用内存使用量逼近并突破 64Mi 限制 |
| 5 | Logging | Elasticsearch | `log.message`: "memory allocation advanced" (`fact-1234f0eb69f1`) | 记录到内存分配行为，且 `allocated_mib` 在 12-34 MiB 间递增 (`fact-numeric`) |
| 6 | Tracing | Tempo | `application_span` GET `/work`: `aiops.observed_mode=oom_growth` (`fact-400f17fa3572`) | 在应用层追踪到内存异常增长的特定模式观测 |

**证据关联性说明：**
- **K8s State** 与 **Metric** 互相印证：OOM 终止原因与内存从 21Mi 攀升至 61Mi 逼近 64Mi 限制的事实完全一致。
- **Tracing** 与 **Logging** 形成闭环：`GET /work` 链路中明确记录了 `oom_growth` 模式，日志中“memory allocation advanced”的具体数值递增提供了发生频率与幅度。

## 🎯 根因分析 · g1

### 因果链

```text
Application logic in /work endpoint causes unbounded memory allocation → Memory usage exceeds container limit of 64Mi → Kernel OOM Killer terminates the process with exit code 137 → Container restart loop (CrashLoopBackOff)
```

### 根因结论

已确认根因为**应用代码在 `/work` 接口处存在内存泄漏**，导致容器内存使用量持续累积，突破 **64Mi** 的硬性限制（`fact-4e0179ac42cc`），触发内核 OOM Killer 强制终止进程（`fact-21f1b06d6c98`），进而引发容器的 CrashLoopBackOff 循环重启。

该结论由以下事实支撑：
1. **Metric (`fact-a1e739ee8dbf`)** 显示工作集内存从 21.7Mi 持续攀升至 61.9Mi，逼近 64Mi 限制。
2. **Tracing (`fact-400f17fa3572`)** 在 `GET /work` 请求中明确记录了 `oom_growth` 观测模式。
3. **Logging (`fact-1234f0eb69f1`)** 记录了多次“memory allocation advanced”日志，显示分配的内存从 12Mi 逐步增加至 34Mi。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 27.3s
├─ 并发证据采集: 95.0s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 95.0s (Evidence 86.0s, RCA 8.8s)
└─ 汇总总结: 11.9s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime, pod-oomkilled
