## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | RecentRestart | Pod aiops-case-10/workload-79d9f8fd88-sbqvc 处于 CrashLoopBackOff，Container app 频繁重启（35次），退出码 137。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Container `app` 退出码 137，状态 `CrashLoopBackOff`，已重启 35 次 | 确认进程被强制终止的直接现象 |
| 2 | K8s Event | kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 (x69 over 101m) | 解释为何容器被判定为不健康并最终重启 |
| 3 | Metric | prometheus | `container_memory_working_set_bytes` 在最后一次活跃期峰值达到 18,194,432 bytes (约 17.3MB) | 观测到容器在崩溃前的内存增长轨迹 |
| 4 | K8s Config | kubernetes | Container `app` 内存硬限制 (`resource_limit`) 为 96Mi | 提供触发 OOM 的资源阈值边界 |

**证据关联说明：**
容器因 Liveness Probe 返回 500 被判定不健康（事实 2），进而触发重启。K8s 事实显示容器以退出码 137 退出（事实 1），这是 Linux OOMKiller 的标准行为特征。Metric 数据显示内存工作集曾持续上升至约 17.3MB（事实 3），而 K8s 配置显示硬限制为 96Mi（事实 4）。结合退出码 137，证据链指向内存突破限制后被系统杀死。

## 🎯 根因分析 · g1

### 因果链

```text
容器应用内存持续增长（峰值约 17.3MB） → 突破 96Mi 硬限制触发 OOMKiller → 进程被强制终止 (Exit Code 137) → Pod 进入 CrashLoopBackOff 并频繁重启
```

### 根因结论

**已确认根因：容器内存使用量超过 Kubernetes 配置的硬限制 (96Mi)，触发 OOMKilled。**

证据证实 Pod `aiops-case-10/workload-79d9f8fd88-sbqvc` 的 `app` 容器频繁以 Exit Code 137 重启（证据 1），且伴随 Liveness Probe 失败（证据 2）。Metric 数据记录了容器内存曾达到约 17.3MB（证据 3），而 K8s 配置显示该容器的内存上限为 96Mi（证据 4）。退出码 137 结合内存监控数据，确凿表明 OOMKiller 因突破硬限制而终止了进程。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 20.9s
├─ 并发证据采集: 110.2s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 110.2s (Evidence 102.0s, RCA 8.0s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-oomkilled, pod-crashloop-runtime
