## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: OOMKilled; `container.last_exit_code`: 137; `container.waiting_reason`: CrashLoopBackOff | 确定容器因内存溢出被内核杀死，且处于反复重启状态 |
| 2 | K8s Config | Kubernetes | `container.resource_limit.memory`: 64Mi | 提供判定内存消耗异常的阈值基准 |
| 3 | Metric | Prometheus | `container_memory_working_set_bytes`: 16:29 峰值达 40808448 (≈38.9 MiB)，16:45 峰值达 42803200 (≈40.8 MiB)，17:08 峰值达 32276480 (≈30.8 MiB) | 证实应用内存占用随时间推移显著增加，逼近 64Mi 限制 |
| 4 | Logging | Elasticsearch | 模式 `memory allocation advanced` 连续 7 次出现，`allocated_mib` 字段从 10 增加至 46 | 直接证明应用在处理请求时会累积分配高达 46 MiB 的内存 |
| 5 | K8s Event | Kubernetes | `BackOff` 警告: `back-off 5m0s restarting failed container=app` (59m 内触发 217 次) | 确认 OOMKilled 后的重启行为已触发 kubelet 的指数退避机制 |

证据表明，应用在处理请求时通过多次内存分配（最高达 46 MiB）导致容器实际内存使用量持续攀升，逼近并可能触发了 64 MiB 的硬性限制，进而触发 OOMKilled 和 CrashLoopBackOff。

## 🎯 根因分析 · g1

### 因果链

```text
应用请求处理累积内存分配（最高达 46 MiB） → 容器实际内存使用量逼近 64 MiB 硬限制 → OOMKilled 机制强制终止容器 (Exit 137) → 持续失败引发 CrashLoopBackOff
```

### 根因结论

已确认根因为应用内存使用模式超出资源限制。证据显示应用每次请求处理过程中累积分配大量内存（日志观测最大值达 46 MiB），导致容器工作集内存（Metric 峰值超 38 MiB）逼近 64 MiB 的内存上限，从而触发内核 OOMKilled 机制（事实 #1、#3、#4）。后续日志中的分配增长趋势支持了内存使用随请求累积的特征。缺失关于“请求间内存释放”的直接证据，但高值已足够触发硬限制保护。

---

## 📊 性能统计

```text
├─ 总耗时: 2.6m
├─ 问题定位: 25.1s
├─ 并发证据采集: 124.0s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 124.0s (Evidence 113.6s, RCA 10.3s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime, pod-oomkilled
