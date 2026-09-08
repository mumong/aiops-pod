## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | 容器内存限制(64Mi)过低，无法承载应用 /work 端点的递增内存分配模式，导致 OOMKilled 和 CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: "OOMKilled" (fact-3b4a7d519340) | 证实容器因内存超限被内核强制终止（Exit Code 137）。 |
| 2 | K8s Event | Kubernetes | `BackOff restarting failed container app` (fact-96eebdbaa433) | 证实容器重启频率极高，符合 OOM 后的 CrashLoop 行为。 |
| 3 | K8s State | Kubernetes | `container.waiting_reason`: "CrashLoopBackOff" (fact-cf147c92f58e) | 当前容器处于因频繁崩溃导致的冷却等待状态。 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory`: "64Mi" (fact-6dbf7e1bed56) | 提供内存硬性约束，对比后续观测值，确认为导致 OOM 的瓶颈。 |
| 5 | Metric | Prometheus | `container_memory_working_set_bytes` 峰值达 `66318336.0` bytes (~63.2Mi) (fact-6494d2bff2ee) | 实际内存使用量已逼近并触及 64Mi 限制，证实资源受限。 |
| 6 | Logging | Elasticsearch | `/work` 端点日志显示 `allocated_mib` 从 10 递增到 46 (fact-1443e3655d81) | 证实应用 `/work` 接口存在递增内存分配模式，且持续消耗直至耗尽。 |
| 7 | Tracing | Deepflow/Tempo | `GET /work` 请求返回 200 (fact-00aa57848b4f) | 请求本身未被拦截，而是运行过程中内存耗尽触发 OOM。 |

**证据关联说明：**
Kubernetes 的 OOMKilled 状态 (Fact 1, 3) 与 Prometheus 观测到的高水位峰值 (Fact 5) 互相印证，说明限制生效。Logging 中的递增分配模式 (Fact 6) 解释了为何请求在短暂运行后会耗尽这仅有的 64Mi 空间，而 Tracing (Fact 7) 确认故障发生在业务逻辑执行期间而非入口阶段。

## 🎯 根因分析 · g1

### 因果链

```text
应用 /work 端点的递增内存分配模式 → 内存使用突破 64Mi 硬限制 → OOMKilled (Exit Code 137) → CrashLoopBackOff
```

### 根因结论

已确认根因为 **容器内存限制过低 (64Mi)**，无法承载应用在 `/work` 端点的内存消耗。
1. **限制与现象匹配**：应用启动并处理 `/work` 请求时（日志 Fact 6），内存使用量迅速增长。
2. **临界点突破**：Prometheus 指标 (Fact 5) 显示工作集峰值达到 ~63.2Mi，极度逼近并触发了 64Mi 的 `resource_limit`。
3. **结果反馈**：Kubernetes 内核检测到越界后终止容器 (Fact 1)，kubelet 触发 BackOff 重启 (Fact 2)，导致当前 `CrashLoopBackOff` 状态 (Fact 3)。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 13.1s
├─ 并发证据采集: 111.5s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 111.5s (Evidence 104.4s, RCA 6.9s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
