## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | OOMKilled | Pod aiops-case-08/workload-5c9c7b6489-wmjhr 持续 CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Exit Code: 137; Container last_terminated_reason: OOMKilled | 明确容器因内存超限被内核 OOM Killer 终止的直接状态 |
| 2 | K8s Config | Kubernetes | container resource_limit.memory: 64Mi; resource_request.memory: 24Mi | 设定了严格的 64Mi 硬限制，为内存溢出提供量化基准 |
| 3 | Metric | Prometheus | `container_memory_working_set_bytes` 峰值从 3.9Mi 增长至 61.9Mi (接近 64Mi 硬限制) | 证实应用运行期间内存占用随时间显著增长并逼近限制 |
| 4 | Logging | Elasticsearch | `memory allocation advanced` 日志 pattern：`allocated_mib` 从 12 增至 42 | 记录应用内部分配内存持续增长，与 Metric 峰值增长相互印证 |
| 5 | Tracing | Deepflow | `GET /work` 请求 9 次 (响应 200)，关联属性 `aiops.observed_mode: oom_growth` | 确认特定业务请求触发了上述内存增长模式，且应用逻辑正常运行直至崩溃 |
| 6 | K8s State | Kubernetes | Container restart_count: 6; Reason: CrashLoopBackOff | 展示因 OOMKilled 导致的 Pod 持续崩溃循环现象 |

**证据说明**：
Metric 显示的内存增长（~62Mi）与 Logging 记录的应用内部内存分配（42Mi）趋势一致，证明内存消耗来自应用本身而非外部注入。Tracing 中的 `oom_growth` 模式明确关联了 `GET /work` 请求与内存增长行为。所有证据均指向内存硬限制（64Mi）无法容纳应用峰值内存需求，从而导致 OOMKilled。

## 🎯 根因分析 · g1

### 因果链
```text
应用启动 OOM 模拟增长模式 (FAILURE_MODE=oom_growth) → 处理 /work 请求时内存持续分配并增长 → 超过 cgroup 硬限制 (64Mi) → 触发内核 OOM Killer (Exit Code 137) → 容器 CrashLoopBackOff
```

### 根因结论
已确认根因为：**容器内存限制（64Mi）过低**。

证据显示，应用在处理 `GET /work` 请求时，其工作集内存（Metric 峰值约 61.9Mi）和内部分配（Logging 最高 42Mi）随请求持续增加，迅速逼近并触发了 64Mi 的硬限制（`container.resource_limit.memory`）。这导致容器被 OOMKilled（退出码 137），进而引发 Pod 的 CrashLoopBackOff 循环。Tracing 中的 `oom_growth` 属性进一步证实了这是受控的内存增长行为，而非异常泄漏或突发攻击。

---

## 📊 性能统计

```text
├─ 总耗时: 11.6m
├─ 问题定位: 18.3s
├─ 并发证据采集: 665.0s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 665.0s (Evidence 653.2s, RCA 11.7s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-oomkilled
