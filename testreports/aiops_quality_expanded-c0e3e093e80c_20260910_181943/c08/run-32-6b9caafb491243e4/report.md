## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | Pod aiops-case-08/workload-5c9c7b6489-p8462 持续处于 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container last terminated reason: OOMKilled (fact-675aae52df92) | 提供直接终止原因 |
| 2 | K8s State | kubernetes | container waiting reason: CrashLoopBackOff; 警告事件 BackOff x378 over 98m (fact-6794045c0b8c, fact-c75724244787) | 确认容器因反复终止而进入重启退避状态 |
| 3 | K8s Config | kubernetes | memory limit: 64Mi (fact-119748140214); exit code 137 (fact-780482646d8b) | 确立硬限制及系统级 OOM 判定依据 |
| 4 | K8s State | kubernetes | restart_count: 20 (fact-1995798165c2); phase Running 但 ContainersReady: False (fact-0247e4210b0a, fact-2b72488863a0) | 表现症状确认 |
| 5 | Metric | prometheus | kube_pod_container_status_last_terminated_reason: 1, label reason=OOMKilled (fact-d09fc98a571f) | 独立确认最近一次终止原因为 OOM |
| 6 | Logging | elasticsearch | 日志 pattern: "memory allocation advanced" 8 次，allocated_mib 从 12 增长至 48 (fact-634896d7988b 聚合) | 证明容器运行期间内存正在持续增长 |

日志中观察到的内存从 12Mi 增长至 48Mi，尽管未达到 64Mi 的硬限制，但 48Mi 已处于接近上限的高水位，且容器随后立即以退出码 137 (OOMKilled) 终止，结合 K8s 状态中的 OOMKilled 原因，确认此次崩溃是由内存限制触发所致。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 内存硬限制仅 64Mi (fact-119748140214) → 应用运行中内存持续增长 (fact-5 Logging, fact-6 Logging) → 触发了 OOMKilled 机制并退出码 137 (fact-1, fact-3) → Pod 进入 CrashLoopBackOff 状态并持续重启 (fact-2, fact-4)
```

### 根因结论

已确认根因是容器 `app` 的内存使用量超过了 Kubernetes 配置的资源硬限制（64Mi），导致内核 OOM 杀手终止了进程。

- **证据支撑**：K8s State 事实 `fact-675aae52df92` 显示容器终止原因为 `OOMKilled`，同时 `fact-780482646d8b` 显示退出码为 137。Prometheus 指标 `fact-d09fc98a571f` 独立佐证了容器最近一次终止原因为 `OOMKilled`。
- **现象形成**：Logging 事实 `fact-5` 显示应用运行期间内存分配量在短期内从 12Mi 增长到了 48Mi。这表明应用在运行过程中产生了较高的内存需求，且已接近 64Mi 的资源上限，最终突破限制导致被强制杀死，进而引发了 `CrashLoopBackOff` (fact-2) 和频繁重启 (fact-4)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 17.5s
├─ 并发证据采集: 58.2s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 58.2s (Evidence 50.4s, RCA 7.7s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
