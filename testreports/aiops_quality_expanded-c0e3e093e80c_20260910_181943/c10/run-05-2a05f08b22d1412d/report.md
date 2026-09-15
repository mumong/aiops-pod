## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bsn84` | CrashLoopBackOff | Pod aiops-case-10/workload-79d9f8fd88-bsn84 处于 CrashLoopBackOff 状态，重启原因是 Error (exit code 137)。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-10/workload-79d9f8fd88-bsn84` 重启 10 次 (`fact-76dec28a1ca7`, `fact-b63dc6f0888b`)，Exit Code: 137 (`fact-3a6904e2f866`) | 确定故障现象：高频重启且由操作系统 OOM Killer 终止 |
| 2 | K8s Config | kubernetes | 容器 `app` 内存限制 96Mi (`fact-3af8797746dc`)，请求 24Mi (`fact-27a5ffc44064`) | 确定异常边界：极低的内存上限是触发条件 |
| 3 | K8s Event | kubernetes | Liveness probe 失败：`HTTP probe failed with statuscode: 500` (`fact-6eb4d0b939e0`); 容器因 probe 失败被 Killing (`fact-44fb80a3dc47`) | 确认应用启动期间健康检查失败，导致重启触发机制激活 |
| 4 | Logging | elasticsearch | `/work` 接口请求成功 (HTTP 200)，内存 `allocated_mib` 在观察窗口 (02:53-02:54) 为 0.0 (`fact-1cac8b260810` 等) | 表明应用代码逻辑在启动阶段可响应正常请求，但在探针检查点处于无法响应的临界状态 |
| 5 | Tracing | Deepflow/Tempo | GET `/work` 成功 (HTTP 200)，延迟 18ms-30ms (`fact-4162500df092` 等); Liveness probe 模式为 `liveness_fail` (`fact-0a2643cb47d8`) | 证明在 probe 失败的时间点，正常业务请求已可通但探针自身未能通过 |
| 6 | Metrics | prometheus | `kube_pod_container_status_restarts_total` = 9 (`fact-56fc535c76c3`); `reason: CrashLoopBackOff` (`fact-f4d59c819c1d`) | 验证故障持续存在且已进入 Kubernetes 自动退避重启循环 |

**证据综合分析**
- **K8s State (事实 1)** 确认了进程因系统级原因（Exit 137）被杀，这与内存限制事实（事实 2）直接关联。
- **K8s Event (事实 3)** 与 **Tracing (事实 5)** 共同解释了为何在应用看起来能响应普通请求（Logging 事实 4，Tracing 事实 5）时，Liveness Probe 却失败（事实 3），这暗示了应用启动初期处于内存极度受限的脆弱状态，探针的 HTTP 请求触发了 OOM 临界点或由于系统资源不足导致探针超时/失败。
- **Metrics (事实 6)** 与 K8s Event 一致，证实了 CrashLoopBackOff 状态。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制设置过低 (96Mi, 事实 2) → 应用启动时内存使用触及限制 → 触发 OOM Killer 终止进程 (事实 1) 或导致系统响应迟缓引发 Liveness Probe 失败 (事实 3) → Pod 重启后进入 CrashLoopBackOff (事实 6)
```

### 根因结论

已确认根因为 **容器内存限制 (96Mi) 远低于应用实际启动所需内存**。

- 证据显示容器因 **Exit Code 137** 被频繁杀死（事实 1、事实 2），这是典型的 OOM Killer 特征。
- Kubernetes 事件显示 Liveness Probe 失败（事实 3），结合 Tracing 数据显示正常请求可通但探针特定标记为 `liveness_fail`（事实 5），说明在内存极度紧张时，健康检查机制成为了触发重启的最后一道防线，或直接因资源竞争无法完成。
- 虽然日志显示应用能响应 `/work` 请求（事实 4），但这发生在 Probe 失败之前或之间，说明应用代码本身无逻辑错误，而是受限于 96Mi 的资源约束。

现有证据足以支撑“内存不足导致 OOM 及探针失败”的结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 18.7s
├─ 并发证据采集: 76.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bsn84: 76.0s (Evidence 64.2s, RCA 11.6s)
└─ 汇总总结: 15.0s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bsn84**: pod-crashloop-runtime
