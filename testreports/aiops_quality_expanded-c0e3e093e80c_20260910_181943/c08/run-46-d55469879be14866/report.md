## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | Pod CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-5c9c7b6489-p8462` 状态 CrashLoopBackOff，容器 `app` 退出码 137，重启 26 次 | 确认当前直接失败现象 |
| 2 | K8s Event | Kubernetes | `Reason: OOMKilled`，伴随 `Back-off restarting failed container app` | 证实容器因内存溢出被 OOM Killer 强制终止 |
| 3 | K8s Config | Kubernetes | 容器 `app` 内存限制 (`resource_limit.memory`) 为 `64Mi` | 确定系统触发终止的阈值 |
| 4 | Metric | Prometheus | `app` 容器内存峰值：`47,013,888` 字节 (≈44.8Mi)，且出现 `47,009,792` 字节 (≈44.8Mi) | 展示应用运行时的内存消耗规模与逼近限制的趋势 |
| 5 | Metric | Prometheus | `app` 容器被 OOMKilled 状态 `kube_pod_container_status_last_terminated_reason` 为 `1` | 从指标维度确证上一次终止原因为 OOMKilled |
| 6 | Logging | Elasticsearch | 日志模式 `http_request ... memory allocation advanced`，分配内存从 `10Mi` 增长至 `48Mi` | 确认触发内存增长的直接行为 |
| 7 | Tracing | Tempo | 请求 `GET /work` 属性标记 `aiops.observed_mode: "oom_growth"`，耗时 `~1ms` | 关联请求路径与 OOM 增长行为的对应关系 |

**证据互证说明：**
Kubernetes 事件 (证据 2) 与指标 (证据 5) 共同证实了系统级 OOM 终止机制的生效。日志 (证据 6) 与 Trace (证据 7) 锁定了导致内存持续增长的具体业务请求路径 (`/work`)。Metric (证据 4) 显示的 `~44.8Mi` 内存峰值，在应用行为 (证据 6) 的上下文下，解释了其如何逼近并触发 `64Mi` (证据 3) 的硬性资源限制，最终导致容器被杀 (证据 1)。

## 🎯 根因分析 · g1

### 因果链

```text
应用请求 /work 持续分配内存 (证据 6, 7) → 内存使用量逼近并触及 64Mi 硬限制 (证据 3, 4) → Kubernetes OOM Killer 终止容器 (Exit Code 137, OOMKilled) (证据 1, 2, 5) → Pod 进入 CrashLoopBackOff 重试循环 (证据 1, 2)
```

### 根因结论

已确认根因为 **应用内存泄漏或设计缺陷**。
在特定请求路径 (`GET /work`) 的持续调用下，应用进程执行了不可控的内存分配（日志记录 `memory allocation advanced`，分配量从 10Mi 增长至 48Mi 以上）。这种线性增长的内存使用最终触及了 Kubernetes 配置的 `64Mi` 硬性限制 (`resource_limit.memory`)，触发 Linux OOM Killer 将容器 `app` 强制终止（退出码 137）。随后 Kubernetes 不断重启该容器，导致其处于 CrashLoopBackOff 状态。

证据链闭环：
- **触发源**：日志与 Trace 证明 `GET /work` 请求伴随内存持续增长 (证据 6, 7)。
- **边界条件**：Pod 配置限制了最大可用内存为 64Mi (证据 3)。
- **最终结果**：K8s 状态与指标确证因超出限制被 OOMKilled，导致 CrashLoopBackOff (证据 1, 2, 4, 5)。

---

## 📊 性能统计

```text
├─ 总耗时: 3.1m
├─ 问题定位: 26.5s
├─ 并发证据采集: 144.6s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 144.6s (Evidence 136.0s, RCA 8.4s)
└─ 汇总总结: 13.5s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
