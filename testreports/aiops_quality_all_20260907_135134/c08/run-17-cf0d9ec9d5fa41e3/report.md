## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | Running | Pod aiops-case-08/workload-5c9c7b6489-wmjhr 频繁重启，状态在 Running 和 CrashLoopBackOff 之间震荡，无法维持正常运行。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubelet | `Back-off restarting failed container app in pod workload-5c9c7b6489-wmjhr_aiops-case-08` (x159 over 46m) | 确认 Pod 持续重启并进入 CrashLoopBackOff 状态 |
| 2 | K8s State | Container | `reason: OOMKilled`, `exit_code: 137` | 确定容器终止原因为内存超限，被系统强制杀除 |
| 3 | K8s Config | Container Limits | `container.app.memory.limit: 64Mi` | 提供判定内存越界的硬限制阈值 |
| 4 | K8s Config | Container Limits | `container.app.memory.request: 24Mi` | 确认请求资源量，突显限制配置较低 |
| 5 | Metric | Prometheus | `container_memory_working_set_bytes`: 观测到 `66056192` bytes (~63Mi) (fact-30cee193e1e5) 和 `59633664` bytes (~57Mi) (fact-4b2f632e869d) | 验证容器工作集内存接近并达到 64Mi 限制上限 |
| 6 | Logging | Elasticsearch | Pattern: `memory allocation advanced`, `allocated_mib` 从 14 跃升至 48 (fact-92b88db3cbb0 等) | 展示应用逻辑中存在导致内存激增的大块分配行为 |
| 7 | Tracing | Deepflow | HTTP GET /work 响应 200, src: `172.16.104.47` -> dst: `172.16.104.42` | 确认异常触发源为 `/work` 接口的持续 HTTP 请求 |

日志中 `/work` 请求单次 `allocated_mib` 最高达 48Mi，结合容器内存限制仅 64Mi，当内存分配加上基础开销时极易突破硬限制；Metrics 记录到的 ~63Mi 工作集内存进一步印证了容器在终止前达到了限制边界，导致 OOMKilled 并触发 Kubelet 的无限重启机制。

## 🎯 根因分析 · g1

### 因果链

```text
应用 `/work` 接口触发大内存分配 (48Mi) → 内存总量超过 64Mi 硬限制 → OOMKiller 终止进程 (Exit 137) → CrashLoopBackOff 循环
```

### 根因结论

根因为 `容器内存配置过低`。
证据链显示应用逻辑（特别是 `/work` 接口）会进行最大约 48Mi 的大块内存分配（日志证据 #6、#7），而该容器被配置的内存硬限制仅为 64Mi（证据 #3）。在运行期间，容器内存使用量多次接近该阈值（Metrics 证据 #5 显示达到 63Mi），导致触及限制被 Linux OOM Killer 强制终止（证据 #2，Exit Code 137, reason OOMKilled）。Kubelet 检测到容器异常退出后不断执行重启策略（证据 #1），致使 Pod 陷入 CrashLoopBackOff 状态，无法维持正常运行。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 17.3s
├─ 并发证据采集: 84.3s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 84.3s (Evidence 75.4s, RCA 8.4s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-oomkilled
