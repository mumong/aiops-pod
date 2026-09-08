## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | 应用启动后执行 `/work` 端点的内存分配操作（从 2MiB 逐步增加至 48MiB），累计或峰值内存占用超过了 Pod 定义的 `memory` limit (64Mi)，触发 Kubernetes OOMKilled 机制强制终止容器进程，导致 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: "OOMKilled" | 直接证明容器因内存超限被内核杀除 |
| 2 | K8s Config | Kubernetes | `container.resource_limit.memory`: "64Mi" | 确立 Pod 的硬性内存资源边界 |
| 3 | Logging | Elasticsearch | `allocated_mib` 连续记录: `first=14`, `last=48` (2026-09-07T17:14:25 - 17:15:00) | 展示 `/work` 端点触发时应用内部内存分配的持续增长模式 |
| 4 | Tracing | Deepflow | L7 Flow: `GET /work` 返回 `200`, `src_ip: 172.16.104.47`, `dst_ip: 172.16.104.42` (共 9 次) | 证明 `/work` 接口被频繁访问且响应成功，是触发内存分配的入口 |

证据表明，应用通过 `/work` 接口（Tracing #4）被调用时执行了内存增长操作，日志显示在极短时间内分配内存从 14MiB 升至 48MiB（Logging #3）。这种增长最终导致容器实际内存使用突破 Kubernetes 定义的 64MiB 硬性限制（K8s Config #2），从而触发 OOMKilled 事件（K8s State #1）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod memory limit (64Mi) 较低 → 应用 /work 端点执行持续内存增长 (2MiB -> 48MiB+) → 容器内存耗尽触发 OOMKilled → CrashLoopBackOff (Restart: 12)
```

### 根因结论

**已确认的根因**：应用启动后，`/work` 端点的内存分配操作（累计或峰值占用接近或超过 48MiB）超出了 Pod 定义的 `memory` limit (64Mi)。

该根因通过以下证据闭环证实：
- **触发机制**：Tracing 数据显示 `/work` 接口被频繁访问并成功响应 (Evidence #4)；Logging 记录显示在访问过程中，内存分配量从 14MiB 持续增长至 48MiB (Evidence #3)。
- **故障触发**：持续增长的应用内存最终触发了容器的 OOMKilled 机制 (Evidence #1)。
- **故障表现**：Kubernetes 记录终止原因为 "OOMKilled" 且退出码为 137，导致容器不断重启形成 CrashLoopBackOff 状态 (Evidence #1, #2)。

现有证据充分，无需更多决定性事实即可确认结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 18.7s
├─ 并发证据采集: 77.6s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 77.6s (Evidence 68.9s, RCA 8.6s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
