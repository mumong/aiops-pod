## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | Pod aiops-case-08/workload-5c9c7b6489-p8462 处于 CrashLoopBackOff 状态，Container app 重启 19 次 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.last_terminated_reason: `OOMKilled` | 直接证明容器因内存超限被系统终止 |
| 2 | K8s Event | kubernetes | Exit Code: `137`, Reason: `CrashLoopBackOff` | 佐证进程被强制杀掉，且重启策略触发 |
| 3 | K8s Config | kubernetes | container.resource_limit.memory: `64Mi` | 提供触发 OOM 的硬性限制基准 |
| 4 | Metric | prometheus | container_memory_working_set_bytes: max `66244608` bytes (~63.1Mi) | 内存工作集持续逼近 64Mi 限制 |
| 5 | Logging | elasticsearch | /work 请求日志中 allocated_mib: `10` -> `48` (last) | 日志确认特定请求处理中内存分配持续增加 |

**证据关联分析：**
Kubernetes 状态确认了“OOMKilled (137)”的终止原因（#1, #2），结合资源限制配置（#3），说明内存不足是直接原因。Metric 观测到峰值内存达到 63.1Mi，极其接近 64Mi 的限制（#4），证实限制被触及。Logging 中 /work 接口处理期间分配的内存从 10Mi 增至 48Mi（#5），揭示了具体的内存增长来源。

## 🎯 根因分析 · g1

### 因果链

```text
Memory Limit 64Mi 设置过低 → /work 业务请求处理导致内存持续分配 → 内存使用量逼近/突破限制 → 触发 OOMKilled (Exit Code 137) → Pod CrashLoopBackOff
```

### 根因结论

已确认根因：容器 `app` 配置的内存硬限制 `64Mi`（`fact-986d24039993`）无法满足应用在处理 `/work` 请求时的内存需求。

证据表明，应用在处理请求时内存分配持续增长，日志显示单次处理涉及的内存分配最高达 48Mi（`fact-1fd114f38ff8` 等），且观测到的内存工作集峰值达到约 63.1Mi（`fact-225dd86f466d`），这直接触发了 Kubernetes 的 OOM Killer（`fact-0802a8cb2598`）。进程退出码 137（`fact-3da8302ff375`）与 OOMKilled 状态一致，并引发了容器的反复重启和 CrashLoopBackOff 状态（`fact-a2bb3b44ecc5`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 15.2s
├─ 并发证据采集: 89.9s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 89.9s (Evidence 78.6s, RCA 11.1s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
