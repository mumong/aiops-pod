## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | 容器内存限制（64Mi）不足导致应用在处理请求时触发 OOMKilled |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason: OOMKilled` (fact-2b00f4923177) | 确证容器因内存不足被 OOM Killer 强制终止。 |
| 2 | K8s Config | Kubernetes | `container.resource_limit.memory: 64Mi` (fact-76e64cfef54b) | 提供导致 OOM 的配置边界事实。 |
| 3 | Logging | Elasticsearch | `allocated_mib` 从 10 增长至 48 (fact-66e0e36251e3 等) | 证明在处理请求 `/work` 时，应用在 38秒 窗口内内存连续分配，逼近 64Mi 硬限制。 |
| 4 | Tracing | Deepflow | `GET /work` 响应 200，耗时 12.8ms-19.1ms (fact-3bc9156d6f6f 等) | 确认业务请求在 OOM 前是正常响应的，且涉及内存分配过程，排除了网络层异常。 |
| 5 | K8s Event | Kubernetes | `Warning  BackOff ... restarting failed container` (fact-da256f10155a) | 描述 Pod 进入 CrashLoopBackOff 状态的实时事件。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason = OOMKilled` (fact-0984ed6cf755) | 辅助确认当前容器的最近终止原因为 OOMKilled。 |

**证据交叉分析：**
日志 (证据3) 与追踪 (证据4) 显示，在 2026-09-07 16:56:22 至 16:57:00 期间，应用处理请求 `/work` 的内存分配量从 10MiB 线性增长至 48MiB。由于容器硬限制仅为 64MiB (证据2)，这一连续增长必然导致容器在后续时刻突破内存上限。Kubernetes 状态 (证据1) 和事件 (证据5) 记录了由此触发的 OOMKilled 和重启行为，形成了完整的“分配增长 -> 触及硬限制 -> OOM 终止”的因果闭环。

## 🎯 根因分析 · g1

### 因果链

```text
容器 memory_limit (64Mi) 配置过低 → 应用处理请求时内存连续分配 (10MiB → 48MiB) → 内存使用触及硬限制触发 OOMKilled → Pod 频繁重启导致 CrashLoopBackOff
```

### 根因结论

已确认根因为**容器内存资源限制（64Mi）不足**。
在请求处理期间，应用进程内存分配量持续增加（日志观测到 `allocated_mib` 从 10 增至 48），逼近并最终突破了 64MiB 的硬限制（K8s Config fact-76e64cfef54b）。这直接导致系统 OOM Killer 介入终止容器（K8s State fact-2b00f4923177），进而引发 Pod 状态显示为 CrashLoopBackOff。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 16.8s
├─ 并发证据采集: 46.8s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 46.8s (Evidence 41.7s, RCA 5.0s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
