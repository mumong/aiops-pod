## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bsn84` | Running | Container app in CrashLoopBackOff (restarts=7, exit_code=137) despite low memory usage |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason: Error`, `container.last_exit_code: 137`, `container.restart_count: 7` | 直接呈现异常现象：容器因错误退出且进程被杀死 (137)，导致重启循环。 |
| 2 | K8s Event | kubernetes | `BackOff: Back-off restarting failed container app...` 在 6m3s 内触发 23 次；`Killing: Container app failed liveness probe, will be restarted` 在 10m 内触发 4 次。 | 描述 Kubernetes 对异常重启的背压响应及 Kill 行为的触发频率。 |
| 3 | K8s Event | kubernetes | `Unhealthy: Liveness probe failed: HTTP probe failed with statuscode: 500` 在 10m 内触发 8 次。 | 直接证明 kubelet 认为探针失败的根本原因是应用侧返回了 HTTP 500。 |
| 4 | Logging | elasticsearch | `request completed` 模式日志中 `http_status: 200`，`allocated_mib: 0` (连续 8 条)。 | 观察窗口内应用能处理正常 HTTP 流量，且无内存分配异常；表明 500 错误并非瞬时内存 OOM 导致。 |
| 5 | Metric | prometheus | `container_memory_working_set_bytes` 当前值 `15421440 bytes` (约 14.7 MB)。 | 确认当前实际内存消耗 (14.7MB) 远低于 `resource_limit` (96Mi)，排除硬内存限制触发 OOM Kill 的可能性。 |

**证据关联说明：**
事件事实 `fact-e18f41b9c92d` 显示 Liveness Probe 返回 500 导致 `fact-fd3a77334855` 的 Killing 事件。由于 Pod 处于 CrashLoopBackOff 状态，应用容器无法接收流量，因此 `fact-0397bfc667a3` 的 Metrics 和 `fact-4f99442cc71a` 的 Logs 仅代表最近一次容器终止前（或重启间隙中）的短暂状态。Log 与 Metric 证明了容器在正常运行时未发生内存溢出或请求失败，从而反向佐证当前 137 退出码和 500 探针错误是由探针配置或应用启动/健康检查逻辑异常引发，而非资源耗尽。

## 🎯 根因分析 · g1

### 因果链

```text
Probe 配置端点(/health)逻辑异常或服务器响应返回 500 → kubelet 判定不健康并执行 kill -9 (SIGKILL) → 容器进程终止并退出(exit_code: 137) → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因是 **Liveness Probe 配置异常或后端端点(/health)服务失败导致持续返回 HTTP 500**。

证据链表明：
1. **明确的不健康原因**：Kubernetes Event (`fact-e18f41b9c92d`) 直接指出 Liveness Probe 的 HTTP 响应码为 500，这是触发后续动作的直接原因。
2. **机制确认**：由于探针持续失败，kubelet 按设计向容器发送 SIGKILL 信号，导致容器以 137 状态码退出 (`fact-64fa688722f0`)，从而进入重启循环。
3. **排除 OOM**：尽管退出码 137 通常与 OOM 关联，但 Metrics (`fact-562858ab7fc1`) 显示容器内存使用 (约 14.7MB) 远低于 Limit (96Mi)，且 Log (`fact-4f99442cc71a`) 显示无异常内存分配。因此，137 仅由 kubelet 的 Kill 行为引起，而非内核 OOM Killer。

---

## 📊 性能统计

```text
├─ 总耗时: 11.7m
├─ 问题定位: 19.6s
├─ 并发证据采集: 671.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bsn84: 671.0s (Evidence 661.0s, RCA 9.8s)
└─ 汇总总结: 13.8s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bsn84**: pod-oomkilled
