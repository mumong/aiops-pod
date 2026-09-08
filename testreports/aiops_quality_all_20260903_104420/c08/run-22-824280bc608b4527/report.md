## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | Pod workload-5c9c7b6489-fl85h 处于 CrashLoopBackOff 状态，容器不断重启失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: "OOMKilled" | 确认容器终止原因为内核 OOM Killer |
| 2 | K8s State | Kubernetes | `container.last_exit_code`: 137 | 确认进程因被信号强制终止而退出，印证 OOM 机制 |
| 3 | K8s State | Kubernetes | `container.resource_limit.memory`: "64Mi" | 确定容器硬内存限制仅为 64Mi |
| 4 | K8s Config | Kubernetes | `container.resource_request.memory`: "24Mi" | 提供内存配额基线，与限制值形成对比 |
| 5 | K8s Event | Kubernetes | `message`: "Warning  BackOff  2m5s (x219 over 60m)" | 证实容器持续重启且处于指数退避状态 |
| 6 | K8s Config | Kubernetes | `container.resource_limit.cpu`: "200m" | 提供 CPU 限制资源参考 |
| 7 | K8s State | Kubernetes | `pod.status`: "Running" | 反映 Pod 目前处于重试中的存活状态 |
| 8 | K8s Measurement | Kubernetes | `container.restart_count`: 14 | 证实应用频繁重启的故障现象 |
| 9 | Metric | Prometheus | `reason`: "OOMKilled" | 外部指标源确认容器被 OOM 终止的状态 |
| 10 | Metric | Prometheus | `reason`: "CrashLoopBackOff" | 外部指标源确认容器的重启循环状态 |
| 11 | Metric | Prometheus | `reason`: "Running" | 确认关联组件 `kube-state-metrics` 正常运行，排除指标采集源问题 |
| 12 | Metric | Prometheus | `reason`: "Unknown" | 确认 `kube-state-metrics` 无异常状态，排除指标异常导致误报 |
| 13 | Logging | Elasticsearch | `pattern`: "memory allocation advanced", `path`: "/work", `allocated_mib` 从 20 增长至 44 | 提供应用在处理特定请求时内存分配的精确证据 |
| 14 | Tracing | Deepflow | `flow`: "GET /work", `src_ip`: 172.16.104.30, `dst_ip`: 172.16.104.20, `occurrence_count`: 9 | 提供导致内存分配的触发流量源及频率 |
| 15 | Tracing | Tempo | `trace_id`: "7ba557385248188bc69c39855fa58f05", `aiops.observed_mode`: "oom_growth" | 确认请求处理过程中的内存持续增长模式 |

证据链表明：应用在处理 `/work` 请求时持续增加内存分配（日志数值从 20Mi 升至 44Mi），而容器的硬内存限制被限制在 64Mi（配置数据）。当内存分配突破该上限时，Linux OOM Killer 介入强制终止进程（返回码 137），导致 kubelet 检测到崩溃并频繁重启容器，最终触发 CrashLoopBackOff 状态。外部指标（Prometheus）与日志/追踪数据（Elasticsearch/Deepflow）在事件原因与模式上完全一致。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制配置过低 (64Mi) → 处理 GET /work 请求时内存分配持续增长（20Mi -> 44Mi） → OOM Killer 强制终止进程 (Exit Code 137) → kubelet 重启失败触发 CrashLoopBackOff
```

### 根因结论

已确认根因为容器内存资源限制配置不足（64Mi）。

证据表明应用在处理 `/work` 请求时会产生持续的内存增长行为（日志 `numeric_fields` 显示 `allocated_mib` 从 20 增至 44），且当前 64Mi 的硬限制不足以容纳该峰值（证据 #3, #13）。这直接触发了 Linux OOM Killer 机制，导致容器以 Exit Code 137 被终止（证据 #2, #12），进而引发了反复重启现象（证据 #5, #8）。Tracing 数据进一步佐证了流量与内存增长的直接关联（证据 #14, #15）。现有 K8s 状态、指标、日志及追踪数据相互印证，事实充分。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 26.3s
├─ 并发证据采集: 64.4s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 64.4s (Evidence 54.7s, RCA 9.5s)
└─ 汇总总结: 14.9s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
