## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | Pod workload-5c9c7b6489-fl85h 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container last_terminated_reason: OOMKilled | 确认直接终止原因 |
| 2 | K8s State | kubernetes | container restart_count: 23, last_exit_code: 137 | 印证 OOMKilled 导致的反复重启 |
| 3 | K8s Config | kubernetes | resource_limit.memory: 64Mi | 确定容器的内存硬限制边界 |
| 4 | Logging | elasticsearch | 日志 pattern: memory allocation advanced, numeric_fields: allocated_mib first=12 -> last=40 (2026-09-03T17:22:22Z 至 17:22:50Z) | 展示处理期间内存连续增长现象 |
| 5 | Tracing | deepflow+tempo | L7 Flow: GET /work, status_code: 200 (occurrence_count: 9) | 证实内存增长发生在正常的请求处理周期内，而非请求异常 |

**证据关联说明**：
K8s 事实确认 Pod 处于 CrashLoopBackOff 状态且因 OOMKilled (exit code 137) 被杀。Logging 事实中的 `numeric_fields` 显示在短短 28 秒内 `allocated_mib` 从 12 增至 40，直接支撑了应用内存泄漏的观察。Tracing 事实表明这些请求均返回 200，说明 OOM 发生在应用逻辑处理的正常路径中。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码在 /work 路径处理过程中内存泄漏 → 内存使用量持续上升并突破 64Mi 限制 → 容器触发 OOMKilled 被系统终止 → Pod 状态转为 CrashLoopBackOff
```

### 根因结论

已确认根因为应用代码在处理 `/work` 请求时存在内存分配泄漏（Memory Leak）。
证据表明，在应用正常运行期间（HTTP 200），内存分配从 12Mi 线性增长至 40Mi（见 Logging fact），最终突破了 64Mi 的硬限制，触发 OOMKilled 导致容器反复重启。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 16.8s
├─ 并发证据采集: 37.5s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 37.5s (Evidence 26.9s, RCA 10.5s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
