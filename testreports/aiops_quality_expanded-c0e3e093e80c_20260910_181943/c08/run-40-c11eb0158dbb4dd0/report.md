## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | Running | 应用存在内存泄漏导致内存持续攀升，最终达到容器内存限制（64Mi）并被 Kubernetes OOM Kill终止 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod phase=Running, container.app wait.reason=CrashLoopBackOff, last_terminated_reason=OOMKilled | 确认容器处于因 OOMKilled 导致的 CrashLoopBackOff 循环中 |
| 2 | K8s State | kubernetes | container.app restart_count=24, last_exit_code=137 (OOMKill) | 确认故障具有高频复现特征且终止原因符合 OOM 机制 |
| 3 | K8s Config | kubernetes | container.app resource_limit.memory=64Mi, resource_request.memory=24Mi | 确认故障边界与容器限制容量一致 |
| 4 | Metric | prometheus | kube_pod_container_status_last_terminated_reason(reason="OOMKilled")=1 | 辅助印证 Kubernetes 层记录的 OOMKilled 终止状态 |
| 5 | Metric | prometheus | kube_pod_container_status_restarts_total=24 | 确认应用重启频率，与 K8s 状态数据一致 |
| 6 | Metric | prometheus | kube_pod_container_status_waiting_reason(reason="CrashLoopBackOff")=1 | 辅助印证 K8s 状态中记录的等待/重启状态 |
| 7 | Logging | elasticsearch | `http_request` pattern `memory allocation advanced` (alloc=38→44Mi) | 观察窗口内存在明确内存增长现象，与资源限制接近 |
| 8 | Tracing | tempo | `GET /work` span 属性 `aiops.observed_mode="oom_growth"` | 应用层链路明确记录并观测到了内存增长行为 |

**证据说明**：
Kubernetes 状态、Metric 及日志数据相互印证了 Pod 因内存耗尽被强制终止并频繁重启的故障现象。Kubernetes 记录的最后终止原因为 `OOMKilled`，Metric 的 `terminated_reason` 标签与之完全一致，重启总数 24 次验证了故障的持续性。日志中 `allocated_mib` 从 38 增长到 44，结合 64Mi 的限制，提供了内存逼近上限的直接行为证据。Tracing 中 `oom_growth` 属性进一步佐证了应用侧内存增长的行为特征。由于 Prometheus 相关趋势查询失败，缺乏内存随时间连续攀升的历史定量证据。

## 🎯 根因分析 · g1

### 因果链

```text
应用内存持续增长 (证据#7, 证据#8) → 耗尽容器内存资源 (受限于 64Mi 硬限制 证据#3) → 触发内核 OOM Kill 机制 (证据#1) → 容器频繁 CrashLoopBackOff (证据#2)
```

### 根因结论

已确认根因为**应用内存泄漏**。

1. **确认事实**：应用在处理 `/work` 请求时存在持续的内存分配增长行为（证据#7、#8），且增长幅度已逼近 64Mi 的容器硬限制。
2. **因果闭环**：内存溢出直接导致 Linux 内核 OOM Killer 介入终止进程（终止码 137 / 证据#1），引发 Pod 重启（证据#2）。
3. **证据完整性**：日志与链路追踪提供了内存增长的直接证据，Kubernetes 状态与 Metric 证实了该增长导致的具体终止后果。缺失的定量证据为 Prometheus 历史 Working Set 趋势，但这并不影响当前“内存超限导致 OOM”这一明确因果链的成立。

---

## 📊 性能统计

```text
├─ 总耗时: 3.1m
├─ 问题定位: 17.6s
├─ 并发证据采集: 159.4s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 159.4s (Evidence 153.0s, RCA 6.3s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-oomkilled
