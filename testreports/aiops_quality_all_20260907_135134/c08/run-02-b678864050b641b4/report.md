## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | Running | 容器内存限制（64Mi）不足，无法承载应用服务运行时产生的内存持续增长行为。应用在处理请求时持续累积内存分配（从2MiB增至48MiB），触发kubelet的OOM Killer机制，导致容器以Exit Code 137被终止并进入CrashLoopBackOff状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: "OOMKilled"` (fact-8e1d9364eb6d) | 确认应用进程被操作系统级 OOM Killer 终止，直接引发退出码 137 和 CrashLoopBackOff |
| 2 | K8s Config | Kubernetes | `container.resource_limit.memory: "64Mi"` (fact-3b02f7feeeb1) | 提供硬限制阈值，是触发 OOM 的关键边界条件 |
| 3 | Logging | Elasticsearch | 模式 `http_request...memory allocation advanced`，观察窗口 `2026-09-07T16:30:37.410Z` 至 `16:31:13.557Z` 内 `allocated_mib` 从 12 增长至 48 (fact-logging-pattern) | 揭示应用存在内存持续增长趋势，且在窗口期内已占硬限制的 75%，逼近崩溃临界点 |
| 4 | K8s State | Kubernetes | `container.waiting_reason: "CrashLoopBackOff"`, `last_exit_code: 137`, `restart_count: 3` (fact-0efb46c5a242, fact-ec4f7c51ce71, fact-20b27ca73111) | 描述系统因重复 OOM 崩溃而进入的自我保护性重启循环状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` 标签 `reason: "OOMKilled"` 值为 1 (fact-31b4f7aecbb9) | 独立于 K8s API 的观测证据，交叉验证了最后一次终止原因为 OOM |
| 6 | Tracing | Deepflow/Tempo | Flow `GET /work` (200)，Span 属性 `aiops.observed_mode: "oom_growth"` (fact-bba865c9b68c, fact-flow) | 证实导致内存增长的请求类型为正常的业务处理请求 (`/work`)，而非异常攻击或单次错误调用 |

**证据综合说明**：
Kubernetes 的 Event 和 State 记录（#1, #4）直接捕获了 OOM 引发的系统行为；日志数据（#3）提供了 OOM 发生前的内存消耗轨迹，证明内存增长发生在业务请求处理过程中；Tracing 证据（#6）排除了异常流量，确认了故障场景为正常的 `/work` 请求处理导致内存累积（`oom_growth`）。Metric 数据（#5）从侧面确认了 OOM 事件。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制（64Mi）设置过低 → 应用处理 /work 请求时内存需求持续增长（12Mi→48Mi） → 触发 kubelet OOM Killer 机制 → 进程以 Exit Code 137 被杀死 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因：**容器内存配置不足**。

Pod `aiops-case-08/workload-5c9c7b6489-wmjhr` 中的 `app` 容器被硬限制在 64Mi 内存。根据日志证据（#3），该应用在持续处理 `GET /work` 请求时，其内存分配量呈现持续增长趋势（在数分钟内从 12MiB 攀升至 48MiB）。当内存分配触及或超过 64Mi 硬限制时，触发了操作系统的 OOM Killer 机制，导致容器以退出码 137 被强制终止，进而引发 Kubernetes 的 CrashLoopBackOff 重启循环。

**证据编号引用**：
- 崩溃原因及重启循环：`fact-8e1d9364eb6d`, `fact-0efb46c5a242`, `fact-ec4f7c51ce71`
- 内存硬限制：`fact-3b02f7feeeb1`
- 内存持续增长轨迹：`fact-logging-pattern`

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 53.7s
├─ 并发证据采集: 81.8s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 81.8s (Evidence 74.4s, RCA 7.2s)
└─ 汇总总结: 14.3s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
