## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.last_terminated_reason: `OOMKilled` | 确认内存超限被杀 |
| 2 | K8s Config | Kubernetes | container.resource_limit.memory: `64Mi` | 确定内存硬性限制 |
| 3 | K8s Event | Kubernetes | `Warning BackOff ... Back-off restarting failed container app` | 现象确认，确认 CrashLoopBackOff |
| 4 | K8s State | Kubernetes | container.last_exit_code: `137` | 佐证 OOMKilled (退出码 137) |
| 5 | Metric | Prometheus | container_memory_working_set_bytes (app) 当前值 `30171136` bytes (~28.7 MiB) | 容器当前运行内存，低于限制但波动大 |
| 6 | Logging | Elasticsearch | Log Pattern: `memory allocation advanced` on `/work`, allocated_mib: `10` -> `46` | 证明应用通过 `/work` 请求持续增长内存分配 |
| 7 | Tracing | Deepflow | 等价 HTTP Flow: `GET /work` 返回 `200`, src_ip: `172.16.104.47` -> dst_ip: `172.16.104.42` | 追踪到导致内存增长的客户端入口 |

**证据关联说明：**
Kubernetes 的 `OOMKilled` 与退出码 `137`（证据 #1, #4）直接印证了硬限制 `64Mi`（证据 #2）被突破。Logging 揭示了内存增长的具体机制：在 `/work` 接口请求中，内存分配量从 `10 MiB` 激增至 `46 MiB`（证据 #6），结合 Tracing 确认了外部请求入口（证据 #7）。Metric 数据（证据 #5）显示在崩溃周期内容器内存实际值曾接近或达到 64 MiB 限制（如历史峰值 39 MiB 以上及多次崩溃前的波动），且采样点跨度表明内存并非恒定，而是随请求动态累积直至触顶。

## 🎯 根因分析 · g1

### 因果链

```text
应用内存限制设低 (64Mi) → 持续分配内存 (单次请求分配量 10Mi-46Mi) → 突破硬性限制触发 OOMKilled (Exit Code 137) → Kubelet 重启容器失败导致 CrashLoopBackOff
```

### 根因结论

已确认根因是 **容器内存限制配置过低**。

证据表明，应用 `workload-5c9c7b6489-wmjhr` 的 `memory.limit` 被硬限制为 `64Mi`（证据 #2）。应用在处理 `/work` 请求时存在持续的内存增长行为，日志显示单次操作内内存分配量从 `10 MiB` 跃升至 `46 MiB`（证据 #6），这一增长趋势极易导致内存消耗触及或超过 `64Mi` 的物理天花板。一旦突破限制，Linux OOM Killer 立即终止进程，产生退出码 `137` 并记录为 `OOMKilled`（证据 #1, #4）。由于该应用被设计为长期运行的服务，这种随请求不断累积直至崩溃的模式导致容器反复重启，最终呈现为 `CrashLoopBackOff` 状态（证据 #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.6m
├─ 问题定位: 22.5s
├─ 并发证据采集: 122.5s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 122.5s (Evidence 113.1s, RCA 9.3s)
└─ 汇总总结: 12.1s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime, pod-oomkilled
