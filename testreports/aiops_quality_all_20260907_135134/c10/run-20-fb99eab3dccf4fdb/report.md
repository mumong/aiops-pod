## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | Pod CrashLoopBackOff, Liveness probe failed: HTTP 500, Exit Code 137 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Liveness probe failed: HTTP probe failed with statuscode: 500` (多次出现, 51m-54m) | 证实 Probe 判定失败直接原因 |
| 2 | K8s Event | Kubernetes | `Container app failed liveness probe, will be restarted` (多次出现, 51m-54m) | 证实 Kubelet 触发 Kill 重启机制 |
| 3 | K8s Event | Kubernetes | `Back-off restarting failed container app` (x170 over 50m) | 证实进入 CrashLoopBackOff 循环 |
| 4 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff` | 证实 Pod 最终状态 |
| 5 | K8s State | Kubernetes | `container.last_exit_code: 137` | 证实容器被强制终止 (OOMKilled/SIGKILL) |
| 6 | Metric | Prometheus | `container_memory_working_set_bytes` (app容器): 3.3MB 升至 15.5MB (`fact-a92781819674`) | 证实容器内存有波动但未突破限制 |
| 7 | K8s Config | Kubernetes | `container.resource_limit.memory: 96Mi` | 提供资源限制边界，排除 OOMKilled (137 常见于 SIGKILL/Probe) |

证据关联与印证说明：
- K8s 事件（#1, #2）与状态（#4, #5）共同印证了“探针失败 -> 杀容器 -> 重启 -> 循环”的完整闭环。
- Metric 显示内存仅升至 15.5MB（#6），远低于 96Mi 的硬限制（#7），佐证退出码 137 并非由 Memory OOM 引起，而是由 Liveness Probe 触发。
- Logging（#7 前略）和 Tracing 展示的是成功请求（HTTP 200 /work），与 Probe 失败的 /health 路径形成限定，说明业务流量正常，问题局限于健康检查逻辑。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness Probe 探测端点 /health 返回 HTTP 500 → 
Kubelet 判定容器不健康并发送 SIGKILL (Exit Code 137) → 
容器不断重启失败 → 
Pod 进入 CrashLoopBackOff 状态，业务不可用
```

### 根因结论

已确认根因为：**Liveness Probe 探测失败（返回 HTTP 500）**。

- **证据支持**：
  1. Kubernetes Events 明确记录 `Liveness probe failed: HTTP probe failed with statuscode: 500` (#1) 及随之而来的 `Container app failed liveness probe` (#2)。
  2. Pod 状态显示 `CrashLoopBackOff` (#4)，且容器退出码为 `137` (#5)，符合被 Kubelet 强制终止的特征。
  3. Metric 内存数据 (#6) 和配置 (#7) 排除了资源耗尽导致的 OOMKilled 可能性，进一步聚焦于 Probe 机制。

- **不确定性**：
  应用内部逻辑导致 `/health` 端点返回 500 的具体原因（如依赖超时、代码 Bug 等）在当前事实中未确认，但属于应用层实现问题，非集群配置或资源故障。

---

## 📊 性能统计

```text
├─ 总耗时: 2.7m
├─ 问题定位: 13.1s
├─ 并发证据采集: 135.4s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 135.4s (Evidence 127.4s, RCA 7.8s)
└─ 汇总总结: 12.2s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-oomkilled, pod-imagepull-failed, pod-crashloop-runtime, pod-config-error, pod-notready-probe-failed
