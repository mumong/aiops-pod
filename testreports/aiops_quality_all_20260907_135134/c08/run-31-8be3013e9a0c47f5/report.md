## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | Pod CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff, `container.last_terminated_reason`: OOMKilled (fact-73d649cf68d0) | 确认容器因内存超限被系统终止 |
| 2 | K8s State | kubernetes | `container.resource_limit.memory`: 64Mi, `container.resource_request.memory`: 24Mi (fact-6a8d7e496492) | 提供导致 OOMKilled 的严格资源限制边界 |
| 3 | K8s Event | kubernetes | `container.last_exit_code`: 137 (Exit Code: 137) (fact-b1b70067ae6a) | 证实容器是被操作系统内核信号（OOM Kill）强制终止 |
| 4 | K8s State | kubernetes | `container.restart_count`: 17, `BackOff` 警告 2m15s (x296 over 80m) (fact-896043b6c4f0) | 描述 CrashLoopBackOff 现象的严重性和持续时长 |
| 5 | Metric | prometheus | `reason: OOMKilled` (fact-9678000b9eb3) | 独立监控数据确认终止原因为 OOMKilled |
| 6 | Metric | prometheus | `restart_count`: 17 (fact-81771e569437) | 与 K8s State 中的重启计数完全一致 |
| 7 | Logging | elasticsearch | Pattern: `memory allocation advanced` (HTTP /work), allocated_mib `first`: 12, `last`: 46 (fact-42a0d2eca737 等) | 直接证明应用在处理请求时内存不断上涨并逼近 64Mi 硬限制 |

**证据关联：**
*   **现象与结果互证**：日志显示内存从 12Mi 增长至 46Mi (证据 7)，逼近并突破 64Mi 的限制 (证据 2)，直接导致系统触发 OOMKilled (证据 1) 并返回 137 退出码 (证据 3)。
*   **监控状态互证**：Kubernetes 状态报告的 17 次重启 (证据 4) 与 Prometheus 采集的重启总数 17 (证据 6) 完全吻合。

## 🎯 根因分析 · g1

### 因果链

```text
内存限制配置严格（64Mi） → 应用处理请求时内存持续上涨触发 OOMKilled → 容器反复崩溃重启 (Exit Code 137) → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因是容器内存硬限制（64Mi）配置过低。
应用在处理 `GET /work` 请求时出现内存增长模式（日志显示分配内存从 12Mi 增长至 46Mi，证据 7），最终突破 64Mi 的硬性边界。这导致操作系统内核以退出码 137（OOMKilled）强制终止容器（证据 1、3），进而使 Pod 陷入 CrashLoopBackOff 状态（证据 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 13.8s
├─ 并发证据采集: 55.3s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 55.3s (Evidence 49.2s, RCA 6.0s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
