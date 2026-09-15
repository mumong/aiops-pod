## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Pod aiops-case-v15/workload 处于 CrashLoopBackOff 状态，容器 app 被反复 OOMKilled (Exit 137) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | Kubernetes | container `app` memory limit: `64Mi` | 证明资源硬限制极小，无法满足常规应用启动需求 |
| 2 | K8s Event | Kubernetes | `Warning BackOff 88s (x395 over 86m)` | 证明容器处于高频重启循环，符合 OOMKilled 后的表现 |
| 3 | K8s State | Kubernetes | terminated reason: `OOMKilled` | 直接指明进程是被操作系统因内存不足强制杀死的 |
| 4 | Logging | Elasticsearch | `startup allocation 256Mi` | 确认应用启动时内存请求远超 K8s 分配的 64Mi 上限 |
| 5 | Metric | Prometheus | `container_restart_total`: `21` (sample_count=1) | 从监控角度佐证重启频率高，验证 K8s 状态的稳定性 |

证据印证逻辑：
容器配置了 `64Mi` 的硬性内存上限，但应用日志明确显示启动需要分配 `256Mi` 内存，导致分配请求超出 cgroup 限制被 OOM Killer 终止。这一过程在 K8s 事件中体现为 `OOMKilled` 以及长达 86 分钟内的 395 次 BackOff 重试，监控指标 `container_restart_total=21` 与 K8s 记录的重启次数一致，共同证实了故障由资源限制不匹配直接引发。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动需 256Mi 内存 → 超出 K8s 配置的 64Mi 硬限制 → 触发 OOM Killer 终止进程 → CrashLoopBackOff 循环
```

### 根因结论

根因为 **应用内存需求与 K8s 资源限制严重不匹配**。
应用启动时强制分配 `256Mi` 内存（见 Logging 证据 #4），而 Kubernetes 配置的 `container.resource_limit.memory` 仅为 `64Mi`（见 K8s Config 证据 #1）。这一硬性限制导致 Linux OOM Killer 介入并终止应用进程，随后 kubelet 按策略不断重启容器，引发 CrashLoopBackOff 状态。该结论由 K8s 状态（OOMKilled, Exit 137）与监控重启计数完全印证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 32.2s
├─ 并发证据采集: 30.4s
│  └─ g1 aiops-case-v15/workload: 30.4s (Evidence 22.6s, RCA 7.6s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
