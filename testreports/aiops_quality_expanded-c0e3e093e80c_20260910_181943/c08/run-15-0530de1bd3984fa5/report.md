## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | Pod workload-5c9c7b6489-p8462 in aiops-case-08 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: OOMKilled; `container.last_exit_code`: 137 | 确定终止原因为内核 OOM Killer 介入 |
| 2 | K8s Config | kubernetes | `container.resource_limit.memory`: 64Mi | 确立触发 OOM 的硬性资源上限 |
| 3 | Logging | elasticsearch | Pattern: `http_request` on `/work`, `allocated_mib` 从 14 升至 48 (观测窗口内连续记录中) | 确认存在随请求增长且未释放的内存泄漏模式 |
| 4 | K8s Event | kubernetes | `BackOff` 警告，198 次 (57m 内)，重启容器 app | 呈现应用因崩溃导致的频繁重启现象 |
| 5 | K8s State | kubernetes | `container.restart_count`: 14 次 | 证实故障的持续性与严重性 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: CrashLoopBackOff | 佐证 Pod 当前处于异常等待状态 |

**证据印证说明：**
Kubernetes 事件与状态事实（证据 #1, #2, #4, #5）一致指向因资源耗尽导致的频繁崩溃重启；日志聚合事实（证据 #3）提供了直接的内存泄漏证据，显示应用在处理特定流量时内存持续增长且突破（或逼近）64MiB 限制，解释了触发 OOMKill 的直接机制。

## 🎯 根因分析 · g1

### 因果链

```text
处理 /work 请求时内存未释放（内存泄漏） → 内存分配持续增长超出 64MiB 硬限制 → 内核 OOMKilled 容器（Exit 137） → Pod 频繁重启进入 CrashLoopBackOff
```

### 根因结论

**已确认的根因**：应用容器 `app` 在处理 HTTP GET 请求 `GET /work` 时存在内存泄漏。
*   **现象机制**：日志证据显示，在观测窗口内，应用在处理 `/work` 请求时分配的内存（`allocated_mib`）从 14MiB 持续上升至 48MiB 且未释放 [证据 #3]。
*   **故障触发**：该持续增长的行为导致内存使用量超过了 Pod Spec 中配置的 64MiB 内存硬性限制 [证据 #2]。
*   **最终结果**：触发 Linux 内核 OOM Killer 机制终止容器（Exit Code 137, OOMKilled）[证据 #1]，进而导致 Kubernetes 不断重启 Pod 陷入 CrashLoopBackOff 状态 [证据 #4, #5]。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 30.6s
├─ 并发证据采集: 78.7s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 78.7s (Evidence 68.1s, RCA 10.5s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
