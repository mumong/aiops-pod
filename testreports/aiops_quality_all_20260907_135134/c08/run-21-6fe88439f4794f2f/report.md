## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | Pod workload-5c9c7b6489-wmjhr (aiops-case-08) 处于 CrashLoopBackOff 状态，持续约 53 分钟，重启 13 次。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: OOMKilled; `container.last_exit_code`: 137 | 确认最近一次崩溃的直接机制是内存耗尽被系统终止 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff; `restart_count`: 13 | 确认因反复崩溃导致的周期性重启状态 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory`: 64Mi | 确认容器内存硬限制，OOMKilled 触发的阈值上限 |
| 4 | Logging | elasticsearch | `allocated_mib`: first=14 → last=48 (pattern: memory allocation advanced) | 日志显示应用每次处理请求时内存使用量显著增加，证实内存线性增长趋势 |
| 5 | Tracing | deepflow | HTTP Flow `GET /work` `response_code`: 200; `span` `aiops.observed_mode`: oom_growth | 追踪显示针对 `/work` 的请求成功返回但伴随内存持续增长模式，关联日志确认泄漏源头 |

上述证据形成闭环：追踪和日志确认 `/work` 接口存在内存持续增长现象（E4），最终内存占用突破 64Mi 限制导致进程被 OOMKilled（E1, E3），进而触发 CrashLoopBackOff 重启循环（E2）。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码在 /work 端点存在内存泄漏 (日志与追踪确认) → 每次请求内存线性增长 (Logging/Tracing) → 容器内存占用超过 64Mi 硬限制触发 OOMKilled (K8s State) → Pod 进程退出进入 CrashLoopBackOff (K8s State)
```

### 根因结论

已确认根因为应用程序代码存在内存泄漏。证据表明，应用在处理 `/work` 请求时内存使用量随请求持续线性增长（E4, E5），最终突破了配置的 `64Mi` 内存硬限制，导致 OOMKilled 机制介入终止进程（E1, E3）。频繁的终止和重启导致了当前的 CrashLoopBackOff 状态（E2）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 19.4s
├─ 并发证据采集: 68.5s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 68.5s (Evidence 59.9s, RCA 8.3s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
