## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | Pod workload-5c9c7b6489-fl85h 处于 CrashLoopBackOff 状态，频繁重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `reason: OOMKilled`, `exit_code: 137` | 确认容器是被系统进程强行终止的 |
| 2 | K8s Config | Kubernetes | `container.resource_limit.memory: 64Mi` | 提供决定性的硬性资源边界依据 |
| 3 | Logging | Elasticsearch | `numeric_fields: allocated_mib` `first: 10`, `last: 46`, `min: 10.0`, `max: 46.0` | 记录日志应用分配内存的显著增长趋势，逼近硬限制 |
| 4 | Metric | Prometheus | `container_memory_working_set_bytes` `max: 57532416.0` (~54.8 MiB) | 实际运行时集内存指标证实容器长期处于高内存占用状态 |
| 5 | K8s Event | Kubernetes | `message: Warning BackOff ... Back-off restarting failed container app` | 记录容器因反复异常退出触发 Kubelet 的退避重启机制 |
| 6 | Tracing | Deepflow | `flow: { "protocol": "HTTP", "request_resource": "/work", "response_code": 200 }`, `occurrence_count: 9` | 证实 OOM 发生前，应用正在持续正常处理并响应 `/work` 路径的请求 |

**证据关联与印证：**
1. 证据 1 和 3、4 高度一致：Pod 的内存硬限制为 64Mi（证据 2），而应用日志记录显示分配的内存从 10Mi 快速攀升至 46Mi（证据 3），且 Prometheus 监控捕捉到的容器最大工作内存峰值达 ~54.8Mi（证据 4），这证实了内存使用的持续消耗正在逼近并最终超过 64Mi 限制。
2. 证据 5、6 结合说明了故障触发机制：在 `/work` 接口持续返回 200 并正常响应的过程中（证据 6），内存消耗不断累积，最终触发 OOMKilled 和退出码 137（证据 1），导致 Kubelet 捕获到终止状态并进入 BackOff 循环（证据 5）。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理 /work 请求时发生内存分配累积 (allocated_mib: 10→46) → 累积内存突破 Pod spec 设定的 memory limit (64Mi) → Linux OOM Killer 强制终止进程 (Exit Code 137, OOMKilled) → Kubelet 进入 CrashLoopBackOff 重启循环 (BackOff event)
```

### 根因结论

已确认根因为：容器 `app` 在处理请求（`/work`）时存在**内存泄漏或持续的高内存消耗行为**。

应用每次请求分配的内存量（日志显示从 10Mi 升至 46Mi）逐渐累积，直接突破了 Kubernetes 配置的 **64Mi** 内存硬限制（`fact-e1014dc0edab`）。这触发了宿主机内核的 OOM Killer 机制，强制杀死了进程（`fact-d4913ecfee41`，`Exit Code: 137`）。随后，Kubelet 尝试重启该容器但因异常重复发生而进入退避等待状态（`fact-8c247c260996`）。证据链完整，排除了资源请求量（24Mi）过低的干扰，明确是实际运行态内存耗尽所致。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 31.7s
├─ 并发证据采集: 86.8s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 86.8s (Evidence 74.9s, RCA 11.8s)
└─ 汇总总结: 12.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime
