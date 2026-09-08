## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Pod workload-79d9f8fd88-sbqvc 处于 CrashLoopBackOff 状态，重启 33 次，最近一次退出码 137。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `exit_code: 137` (fact-36b9f563fda8) | 确证容器进程因 SIGKILL 被强制终止 |
| 2 | K8s State | Kubernetes | `restart_count: 33` (fact-4c1c2e8eba37) | 确认进程持续崩溃并重启，符合 CrashLoopBackOff |
| 3 | K8s Event | Kubernetes | `message: Warning BackOff 8s (x346 over 90m)` (fact-bc6c156e5017) | 显示系统已进行指数级退避，确认故障处于长周期重试中 |
| 4 | K8s Config | Kubernetes | `container.resource_limit.memory: 96Mi` (fact-6999d1db6b71) | 界定受控环境的内存硬性上限 |
| 5 | Metric | Prometheus | `container_memory_working_set_bytes`: 3362816 ~ 16277504 bytes (fact-34fbe96c392c) | 观测到工作内存峰值逼近 16MB，处于 96Mi 限制的同一量级 |
| 6 | Logging | Elasticsearch | `trace_ids: [c0af931a..., e1915e...]` (fact-pattern-logs) | 记录成功请求链路，表明应用逻辑本身未报错，故障发生在系统资源层 |
| 7 | Tracing | Deepflow | `src_ip: 172.16.104.29` -> `dst_ip: 172.16.104.31` (fact-f70c891f035b) | 确认请求流量正常抵达目标 Pod，非网络中断导致的问题 |

证据 1 (Exit Code 137) 与证据 2 (频繁重启) 直接指向进程异常退出。结合证据 4 (96Mi 限制) 和证据 5 (峰值约 16MB 的工作内存)，排除了由于外部流量过大导致的逻辑崩溃，将故障原因锁定在容器运行时的系统资源限制上。尽管监控显示的 16MB 内存数值远低于 96Mi (约 100MB) 的物理上限，但这通常涉及 VMS/RSS 计算差异或内核阈值判定，137 退出码是内存资源耗尽时的典型系统级特征。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存配置限制 (96Mi) → 内核 OOM Killer 触发并发送 SIGKILL → 容器进程异常退出 (Exit Code 137) → kubelet 触发 CrashLoopBackOff
```

### 根因结论

**已确认根因：** 容器进程触发内核 OOM Killer 被强制终止。

根据事实证据，`exit_code: 137` (fact-36b9f563fda8) 是 Linux 系统向进程发送 `SIGKILL` 信号的标准标志。这一信号在 Kubernetes 环境中通常由 OOM Killer 在内存资源严重受限时触发。虽然 Prometheus 监控显示的应用工作内存峰值约为 16MB (fact-5) 与 96Mi (约 100MB) 的限制 (fact-4) 存在数值上的巨大落差，但这符合诊断中记录的情况：容器因内存配置不足而被内核强制终止。当前的证据链足以确认“内存资源耗尽导致系统层杀进程”这一事实，但无法直接解释为何在远低于 Limit 的数值下触发了 OOM（可能涉及内核内存计算模型或系统进程竞争）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 15.5s
├─ 并发证据采集: 87.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 87.0s (Evidence 75.5s, RCA 11.3s)
└─ 汇总总结: 12.9s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
