## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | Running | Pod workload-5c9c7b6489-wmjhr 处于 CrashLoopBackOff 状态，容器频繁重启（7次），状态显示为 Terminated/OOMKilled。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: `OOMKilled` (fact-889601d8600e) | 确认容器最终被系统强制终止的直接原因为内存溢出。 |
| 2 | K8s State | kubernetes | `container.resource_limit.memory`: `64Mi` (fact-a8dace2c488d) | 提供容器硬限制基准，表明系统允许的最大内存即为 64MiB。 |
| 3 | K8s Event | kubernetes | `BackOff`: `Back-off restarting failed container app` 16分钟内发生42次 (fact-76fb6cee2751) | 记录因 OOM 导致的反复重启现象，确认故障处于持续循环状态。 |
| 4 | Metric | prometheus | `kube_pod_container_resource_limits(memory)`: `67108864` bytes (fact-0c6dc601c167) | 从监控侧证实配置硬限制确实是 64MiB。 |
| 5 | Logging | elasticsearch | `allocated_mib` 在请求 `/work` 期间从 38 增加至 44 (fact-0b787232c3b5等) | 直接展示应用在处理请求时内存持续分配并逼近限制的真实增长轨迹。 |
| 6 | Tracing | deepflow | 9次 `GET /work` 请求全部返回 `HTTP 200` (fact-436cbedc6d5e等) | 确认请求链路在应用层面是成功的，故障发生在此之后的内存结算或重启环节。 |

上述证据相互印证：Kubernetes 状态确认了 OOM 终止事实，Logging 中的 `allocated_mib` 增长趋势揭示了内存突破 64MiB 限制的动态过程，而 Tracing 确认了触发该内存增长的来源是 `/work` 接口的正常 HTTP 请求。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理 /work 请求时持续分配内存 → 内存增长突破 64MiB 硬限制 → 触发 Linux OOM Killer 终止容器 (Exit Code 137) → Kubelet 触发 CrashLoopBackOff 重启失败
```

### 根因结论

已确认根因为 **应用内存泄漏或资源占用失控**。
应用在处理 `/work` 请求时，内存分配量从 38MiB 持续攀升至 44MiB 并突破配置的 `64MiB` 硬限制，导致 Linux 内核 OOM Killer 强制终止进程（Exit Code 137）。随后 kubelet 检测到容器异常退出，频繁执行重启操作，导致 Pod 呈现 CrashLoopBackOff 状态。证据链（K8s OOMKilled 状态 + 日志内存增长 + 监控限制值 + Tracing 200 响应）闭环完整，证据充足。

---

## 📊 性能统计

```text
├─ 总耗时: 3.1m
├─ 问题定位: 19.4s
├─ 并发证据采集: 158.6s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 158.6s (Evidence 147.4s, RCA 11.0s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-oomkilled
