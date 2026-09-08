## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | Pod workload-5c9c7b6489-wmjhr处于CrashLoopBackOff状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (fact-456a94c3a63f) | container.app last_terminated_reason: "OOMKilled" | 确认进程被系统终止的直接原因 |
| 2 | K8s State | kubernetes (fact-8670afa9fec2, fact-c6bf628ce869) | Pod 状态与退出码: Reason="OOMKilled", Exit Code="137" | 佐证系统级 OOM 终止事实 |
| 3 | K8s Config | kubernetes (fact-7ddee0bd2d2b) | container.app 内存硬限制 (resource_limit.memory): "64Mi" | 确立内存资源硬约束基线 |
| 4 | Logging | elasticsearch (pattern: http_request) | 请求日志 "memory allocation advanced" 中 allocated_mib 从 10 增至 46 | 证明应用处理请求时存在持续内存增长 |
| 5 | Tracing | deepflow (l7_flow) | HTTP GET /work 流量记录 (9次)，响应状态 200 | 证明应用处于正常工作调用链中，非逻辑死循环 |

**证据印证分析：**
- **K8s 与 Metric 的印证**：K8s 提供的 `reason=OOMKilled` (E#1) 和 `exit_code=137` (E#2) 与 Metrics 中 `kube_pod_container_status_last_terminated_reason` 为 `OOMKilled` 完全一致。
- **现象与配置的冲突**：应用虽然在正常工作（HTTP 200，E#5），但日志显示内存申请持续增加（E#4）。由于日志中 `allocated_mib` 已增至 46 MiB，且硬限制仅为 64 MiB (E#3)，这种增长在多次请求后必然触发 E#1 和 E#2 中的 OOM 终止。
- **因果闭环**：高增长的内存申请（E#4）超出了固定的低限制（E#3），导致容器被系统杀掉（E#1/2），形成 CrashLoopBackOff 循环。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理HTTP请求时内存持续增加（E#4: allocated_mib 从10增至46） → 
容器内存占用逼近并超过64Mi硬限制（E#3） → 
容器被系统OOMKilled终止（E#1, E#2: exit code 137） → 
Pod进入CrashLoopBackOff状态（待验证重启机制，基于K8s状态E#1/E#2推断）
```

### 根因结论

已确认的根因为：**容器内存限制（64Mi）过低与应用内存持续泄漏（未释放）的矛盾。**

具体表现为：
1. **资源限制过窄**：容器 `app` 的内存硬限制仅为 64Mi (E#3)。
2. **异常内存行为**：在应用正常工作（HTTP 200, E#5）的前提下，日志显示内存申请量在处理请求时持续增加（E#4），且当前已占用至 46 MiB。
3. **直接失效机制**：持续增长的内存最终超过了 64 MiB 的限制，触发 Linux OOM Killer，以退出码 137 终止容器（E#1, E#2）。

现有证据足以确认“内存超限导致被杀”这一故障链，但具体的代码级泄漏原因（如未关闭的流、缓存未清理等）属于已知未知项（Unknowns），需后续深入应用内部排查。

---

## 📊 性能统计

```text
├─ 总耗时: 2.6m
├─ 问题定位: 24.7s
├─ 并发证据采集: 117.9s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 117.9s (Evidence 108.0s, RCA 9.8s)
└─ 汇总总结: 12.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
