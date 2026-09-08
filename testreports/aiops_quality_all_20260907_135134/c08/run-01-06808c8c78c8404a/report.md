## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | Running | Pod workload-5c9c7b6489-wmjhr 处于 Running 状态，但容器未 Ready（restarts=1, BackOff），由上一次 OOMKilled 导致重启失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Back-off restarting failed container app` | 确认应用重启陷入 BackOff 循环 |
| 2 | K8s State | kubernetes | `last_terminated_reason: OOMKilled` | 提供终止原因的直接证据 |
| 3 | K8s State | kubernetes | `last_exit_code: 137` | 确认 OOMKilled 终止状态 |
| 4 | Metric | prometheus | `container_memory_working_set_bytes` (重启前): `first=21MiB`, `last=59MiB` (max 61956096 bytes) | 证实内存使用呈线性增长趋势 |
| 5 | Metric | prometheus | `container_memory_working_set_bytes` (重启后): `first=3.6MiB`, `last=54.8MiB` (max 57536512 bytes) | 证实重启后再次触发内存激增 |
| 6 | K8s Config | kubernetes | `container.resource_limit.memory: 64Mi` | 定义硬限制，为 OOMKilled 提供阈值上下文 |
| 7 | Logging | elasticsearch | 模式 `memory allocation advanced` (8次), `allocated_mib`: `first=4`, `last=38` | 揭示应用日志中的内存分配行为与 Metrics 增长吻合 |
| 8 | Tracing | deepflow | HTTP GET /work (8次), 响应状态 200 | 关联触发内存分配的具体操作 |

**证据印证关系：**
Kubernetes 的 OOMKilled (证据2) 与退出码 137 (证据3) 提供了故障终止状态；Metric 证据 4 和 5 显示应用重启前/后内存工作集均逼近 64 MiB 限制（证据6）；日志证据 7 中的分配行为解释了内存增长来源，而 Tracing 证据 8 将增长行为锚定在 `/work` 请求的处理路径上。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理 /work 请求时持续分配内存 → 容器内存工作集线性增长触及 64MiB 硬限制 → kubelet OOMKilled 容器 app (exitCode 137) → Pod 处于 Running 但 NotReady (BackOff)
```

### 根因结论

应用在处理 `/work` 请求时存在持续内存分配行为（日志模式与 Metrics 增长趋势吻合），导致容器内存使用量不断攀升并触及 `64Mi` 的资源限制。Kubelet 随后执行 OOMKilled (Exit Code 137) 终止了该容器，由于重启后内存分配行为未消除，Pod 再次崩溃并进入 BackOff 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 19.6s
├─ 并发证据采集: 98.7s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 98.7s (Evidence 86.8s, RCA 11.7s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-oomkilled, pod-terminating-stuck
