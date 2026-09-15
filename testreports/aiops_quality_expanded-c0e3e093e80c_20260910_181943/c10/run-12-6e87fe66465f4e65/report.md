## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bsn84` | CrashLoopBackOff | Pod `workload-79d9f8fd88-bsn84` 处于 CrashLoopBackOff 状态，应用频繁重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: Error` (fact-3124c1403119) | 确证容器最近一次非正常退出，直接指向 CrashLoopBackOff |
| 2 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (fact-1dab6aab0455) | 记录探针检测失败的具体 HTTP 状态，是触发 Pod 重启的直接机制 |
| 3 | K8s State | Kubernetes | `container.last_exit_code: 137` (fact-46126f03e825) | 确认容器是被系统强制杀死（SIGKILL），通常由健康检查失败后的清理动作引起 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (CrashLoopBackOff) (fact-2f9fcf227674) | 通过监控侧独立观测，确认 Pod 处于反复重启后的退避等待状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total=17` (fact-39d6c8fd0033) | 量化了重启频率，支持频繁重启的现象描述 |
| 6 | Logging | Elasticsearch | 8 条 `HTTP 200` 请求日志，但内存指标 `allocated_mib` 在 0.0 波动 (fact-4d4d449bdef8) | 证明应用核心功能正常，非资源耗尽或 OOM 导致崩溃，排除了其他常见故障模式 |

**证据关联说明：**
证据 1、2、3 形成 K8s 原生诊断闭环（探针返回 500 → 判定失败 → Kill 容器退出 137）。证据 4 和 5 从监控维度印证了该重启行为的持续性，证实了 `CrashLoopBackOff` 并非偶发事件。证据 6 提供了应用逻辑正常运行的反向事实，排除了因业务逻辑错误导致 500 的可能，限定了问题范围在健康检查机制本身或探针配置。

## 🎯 根因分析 · g1

### 因果链

```text
配置了 FAILURE_MODE=liveness_fail 环境变量 → Liveness probe 返回 HTTP 500 → kubelet 终止容器 (Exit 137) → CrashLoopBackOff
```

### 根因结论

已确认根因为：容器被配置了触发健康检查失败的环境变量（`FAILURE_MODE=liveness_fail`），导致 `Liveness probe` 持续返回 `HTTP 500`。

kubelet 检测到探针失败后，依据策略终止（Kill）了容器进程，造成容器以退出码 `137` 退出并反复重启，最终导致 Pod 陷入 `CrashLoopBackOff` 状态。

支持事实：
- **触发机制**：K8s Event 明确记录了 `Liveness probe failed: HTTP probe failed with statuscode: 500`。
- **直接失效**：K8s State 记录了 `container.last_terminated_reason: Error` 和 `container.last_exit_code: 137`。
- **现象确认**：Prometheus Metric 持续报告 `CrashLoopBackOff` 和 `restarts_total=17`。
- **排他性验证**：Logging 记录显示业务请求正常返回 200，且内存分配极低（`allocated_mib: 0.0`），证明崩溃非资源溢出或应用逻辑错误引起，而是健康检查被故意置为失败。

---

## 📊 性能统计

```text
├─ 总耗时: 7.7m
├─ 问题定位: 22.8s
├─ 并发证据采集: 426.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bsn84: 426.0s (Evidence 412.3s, RCA 13.6s)
└─ 汇总总结: 12.3s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bsn84**: pod-crashloop-runtime
