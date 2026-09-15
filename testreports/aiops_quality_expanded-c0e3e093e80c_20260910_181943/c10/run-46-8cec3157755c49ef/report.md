## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | RecentRestart | Pod workload-79d9f8fd88-48j8r 处于 CrashLoopBackOff 状态，容器持续重启，退出代码 137 (SIGKILL)。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Exit Code: 137 (Exit Code: 137) | 确定异常终止原因，Exit 137 表示容器进程被 SIGKILL 强制杀死 |
| 2 | K8s State | kubernetes | Restart Count: 27 | 证实存在频繁的 CrashLoopBackOff 状态，验证持续性异常 |
| 3 | K8s Config | kubernetes | Memory Limit: 96Mi | 提供关键资源上下文，存在极高的内存受限嫌疑 |
| 4 | K8s Event | kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 | 提供直接失败前的状态证据，探针超时失败导致触发重启机制 |
| 5 | Logging | elasticsearch | request completed, http_status: 200, allocated_mib: 0.0 (min 0.0, max 0.0) | 表明在正常时段应用运行且无内存分配，但结合 137 异常终止，存在资源断崖式耗尽的可能 |
| 6 | Tracing | deepflow | HTTP GET /work, src_ip: 172.16.104.33, dst_ip: 172.16.104.34, response_code: 200 | 证实网络层面的服务连通性在无异常期间正常，排除网络不通导致的探针失败 |

证据 1 (Exit Code 137) 与证据 3 (96Mi 内存限制) 构成了典型的 OOM Kill 证据链，Exit 137 是 OOM Killer 动作的直接后果；证据 4 (探针 500) 解释了重启的直接触发器，而证据 5 (内存分配为 0) 与证据 6 (正常 HTTP 200) 说明在正常运行窗口内服务并未出现常规的资源增长或报错，支持了内存突发耗尽导致进程被系统强制终止的假设。

## 🎯 根因分析 · g1

### 因果链

```text
容器进程内存/资源突发耗尽 (未确认根因类型) → 被系统 OOM Killer 强制终止 (SIGKILL/Exit 137) → Kubelet 检测退出并触发 Liveness Probe 失败 (HTTP 500) → Pod 进入 CrashLoopBackOff 状态 (重启 27 次)
```

### 根因结论

已确认根因：容器进程 `app` 被操作系统强制终止（SIGKILL，Exit Code 137），直接导致 Liveness Probe 失败（HTTP 500），进而触发 Kubernetes 的 CrashLoopBackOff 重启机制。

结合该容器仅有 `96Mi` 的内存限制（证据 3）以及 `allocated_mib` 历史数据无显著增长（证据 5），推测极有可能是内存耗尽触发了 OOM Killer。但受限于缺乏节点层面的 `dmesg` 或 `journalctl` 系统日志，无法确证具体的 OOM 记录，也无法排除其他导致 SIGKILL 的外部因素。因此，根本性质为**“由资源瓶颈或异常引起的进程被系统强制终止”**。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 23.1s
├─ 并发证据采集: 107.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 107.0s (Evidence 96.5s, RCA 10.4s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime, pod-oomkilled
