## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | RecentRestart | Pod workload-79d9f8fd88-bwqhh 处于 CrashLoopBackOff 状态，容器重启 5 次，退出码 137，Liveness Probe 失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `exit_code: 137` (fact-0c9397740b49); `reason: CrashLoopBackOff` (fact-ddb89ab0e43b); `restart_count: 5` (fact-2bfac5c16e22) | 直接事实：容器以信号终止（137），进入重启循环。 |
| 2 | K8s Config | Kubernetes | `memory_limit: 96Mi` (fact-098540bc30b5); `memory_request: 24Mi` (fact-ab5aecf85299) | 背景：存在 24Mi 内存硬限制。 |
| 3 | K8s Event | Kubernetes | `Liveness Probe 失败` (phenomenon) | 现象：存活探针未通过，触发重启。 |
| 4 | Logging | Elasticsearch | 日志显示 `http_status: 200` (fact-0819543d0683); `allocated_mib: 0` (fact-0819543d0683) | 背景：在采样窗口内应用 HTTP 请求处理正常，日志中未捕获到内存溢出相关的报错（如 OOM）。 |
| 5 | Tracing | Deepflow | 流量记录 `GET /work` 响应码 `200` (fact-525207a11b5f) | 支持：网络层观测到请求已成功返回，未记录连接重置或失败。 |

**证据关系说明**
- 编号 1 的 `exit_code: 137` 是确认容器被强制终止的**核心事实**，该代码在操作系统层面唯一对应 `SIGKILL` 信号（常见于 OOM Killer 或外部强制终止）。
- 编号 2 的 `96Mi` 内存限制为排查 137 终止码提供了必要的**上下文**（内存溢出是一种合理的 OOM 假设）。
- 编号 3、4 和 5 共同表明：在故障发生前后的可观测采样窗口内，应用本身**并未暴露**出明显的内部错误或内存耗尽日志（`allocated_mib` 均为 0，且返回 200 状态码）。
- 现有证据证实了“容器被强杀”的现象，但日志中缺失内存指标上升或 `killed` 字样的记录，导致暂时无法在日志侧确认是内部 OOM 还是外部干预。

## 🎯 根因分析 · g1

### 因果链
```text
容器进程接收 SIGKILL 信号（Exit Code 137） → 容器被操作系统级强制终止 → Kubelet 发现容器退出且存活探针（Liveness Probe）失败 → Kubernetes 触发重启（CrashLoopBackOff）
```

### 根因结论
- **已确认的机制**：Pod `workload-77d9f8fd88-bwqhh` 的 `app` 容器正经历 **CrashLoopBackOff**，其直接原因为容器进程收到了 **`exit_code: 137`**。该退出码在 Kubernetes 诊断中明确指示容器进程收到了 `SIGKILL` 信号并被终止，同时由于存活探针探测失败，导致了 5 次重启。
- **证据不足**：当前缺乏区分 `SIGKILL` 具体来源的决定性事实。虽然配置中存在 `memory_limit: 96Mi`（可能暗示 OOM Kill），但在现有的 Elasticsearch 日志采样（`fact-0819543d0683`）中，并未观察到内存增长记录（`allocated_mib` 均为 0）或明确的 OOM 报错文本；Tracing 数据（`fact-525207a11b5f`）仅显示成功响应。由于未采集到宿主机层面的 `dmesg` 或 Kubelet 内部 `OOM Kill` 日志，**无法确诊是否为内存溢出**，亦无法排除外部强制杀进程的可能性。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 18.7s
├─ 并发证据采集: 102.1s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 102.1s (Evidence 92.1s, RCA 9.8s)
└─ 汇总总结: 13.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-oomkilled
