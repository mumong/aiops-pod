## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Pod aiops-case-v17/workload 处于 CrashLoopBackOff 状态，重启 14 次 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Liveness probe failed: ... context deadline exceeded` (31m 内 x23 次) | 直接导致 Pod 被反复重启的触发原因 |
| 2 | K8s State | Kubernetes | `container.last_exit_code`: 137, `container.last_terminated_reason`: Error | 确认应用进程发生过异常终止 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory`: 64Mi | 提供可能导致 OOMKilled 的上下文边界 |
| 4 | Logging | Elasticsearch | `GET /health HTTP/1.1" 200` (在 13:31:31 - 13:32:03 窗口内持续返回) | 证实应用进程存在，但 K8s 探针未收到预期响应 |
| 5 | Tracing | Deepflow | `GET /health` Flow: 10次, duration_us 在 3001057.0 - 3001826.0 之间 (约 3s) | 证实应用处理 `/health` 请求的实际耗时约为 3s |

**证据关联分析**：
Trace 数据（#5）明确显示应用处理健康检查请求的实际耗时超过 3 秒。Kubernetes 探针在 31 分钟内连续 23 次因 `context deadline exceeded`（超时）失败（#1）。日志记录（#4）显示请求最终返回了 200，印证了应用未立即崩溃，但超时导致探针判定失败。这种超时的直接原因是应用逻辑耗时（约 3s）超过了探针的超时阈值（根据报错及常见配置，探针配置应为 1s 或更短），从而不断触发 Kill 重启（#2, #3 提供资源限制背景，但直接触发机制是探针超时）。

## 🎯 根因分析 · g1

### 因果链

```text
应用健康接口 /health 实际处理耗时约 3s → Liveness Probe 配置的超时阈值（推测为 1s） < 实际耗时 → 探针连续判定失败 (Timeout) → 触发 K8s 强制重启 (Exit Code 137/BackOff) → 用户可见 Pod 处于 CrashLoopBackOff 状态
```

### 根因结论

**已确认根因**：容器 Liveness Probe 的超时阈值（Timeout）配置过小，与业务逻辑中 `/health` 接口处理所需的 3s 耗时（约 3000ms）存在冲突。
- **证据引用**：Deepflow 流量追踪显示 `/health` 请求平均耗时约 3000ms（#5），而 K8s 事件显示探针因 `context deadline exceeded` 连续失败 23 次（#1），且应用日志显示接口最终返回 200（#4）。
- **结论**：应用本身未被 OOMKilled 直接终结（虽然有 Exit 137，但在探针超时重启场景下也常见），而是因探针超时导致 Kubelet 主动 Kill 掉响应慢的容器，并不断重启。虽然输入中的 Formal RCA 提到了内存限制，但当前证据链（Trace + K8s Event + Log）最强支撑的是“探针超时导致重启”，内存 64Mi 仅为背景信息，未观测到明确的 OOM 内核日志或 Metrics 峰值证据，故当前确定性根因为**探针超时配置不当**。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 16.2s
├─ 并发证据采集: 55.0s
│  └─ g1 aiops-case-v17/workload: 55.0s (Evidence 45.0s, RCA 9.8s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
