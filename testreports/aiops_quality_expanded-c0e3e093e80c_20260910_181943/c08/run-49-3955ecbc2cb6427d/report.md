## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | Pod workload-5c9c7b6489-p8462 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.last_terminated_reason="OOMKilled" (fact-0860ce31d586) | 确认应用容器因内存溢出被强制终止的根因 |
| 2 | K8s Event | kubernetes | BackOff 4m49s (x553 over 148m) restarting failed container app (fact-197cf0cb500c) | 描述 Pod 处于 CrashLoopBackOff 状态及频繁重启的现象 |
| 3 | K8s Config | kubernetes | container.resource_limit.memory="64Mi" (fact-6f4d7e123192) | 提供容器内存硬限制阈值，用于界定溢出范围 |
| 4 | Metric | prometheus | kube_pod_container_status_last_terminated_reason="1" (reason="OOMKilled") (fact-ed39210a9765) | 验证终止原因与 K8s 状态事实一致 |
| 5 | Logging | elasticsearch | 日志模式 "memory allocation advanced" 中 allocated_mib 从 14Mi 增长至 36Mi (fact-26d2e48ea8d0等) | 证明应用在处理 /work 请求时内存呈持续增长趋势 |
| 6 | Tracing | deepflow+tempo | HTTP GET /work 请求流量，span 标记 aiops.observed_mode="oom_growth" (fact-51c195524e60) | 关联业务请求与内存异常增长，提供因果上下文 |

**证据说明：**
1. K8s 的 `OOMKilled` 终止原因与 Prometheus 指标 `terminated_reason` 相互印证，确认故障的直接诱因是容器内存超限。
2. 日志中 `allocated_mib` 的数值增长（14Mi → 36Mi）与 Tracing 中标记的 `oom_growth` 模式结合，明确了异常行为发生在处理 `/work` 请求的过程中。
3. 结合 64Mi 的内存限制与持续增长的趋势，证实应用内存最终突破了容器上限导致 OOM。

## 🎯 根因分析 · g1

### 因果链

```text
应用持续处理 /work 请求（日志显示内存分配增长，Tracing 标记 oom_growth） → 内存使用量突破容器 memory limit (64Mi) 的硬限制 → 内核触发 OOM Killer 终止容器 (exitCode 137, OOMKilled) → Pod 进入 CrashLoopBackOff 并频繁重启 (BackOff Event)
```

### 根因结论

**已确认根因：** 应用在处理 `/work` 请求时存在内存持续增长的行为，最终突破了 Kubernetes 分配的容器内存硬限制（`memory_limit: 64Mi`），导致内核 OOM Killer 杀死进程（`OOMKilled`）并触发 CrashLoopBackOff 重启循环。

**证据支持：**
- 终止根因：`OOMKilled` (fact-0860ce31d586, fact-ed39210a9765)
- 资源限制：内存上限 64Mi (fact-6f4d7e123192)
- 增长趋势：日志内存字段持续升高 (fact-26d2e48ea8d0等)，Tracing 标记为 `oom_growth` (fact-51c195524e60)
- 用户现象：BackOff 事件与 Pod 重启计数 (fact-197cf0cb500c, fact-c048bed423ee)

---

## 📊 性能统计

```text
├─ 总耗时: 10.2m
├─ 问题定位: 23.2s
├─ 并发证据采集: 575.4s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 575.4s (Evidence 568.8s, RCA 6.5s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
