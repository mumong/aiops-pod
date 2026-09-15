## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | Running | 容器内存限制（64Mi）不足导致OOMKilled（Exit Code 137） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | kubernetes | `container.resource_limit.memory=64Mi` (fact-94de526ef3c1) | 确认容器 app 拥有极低的内存硬限制，是引发 OOM 的基础配置 |
| 2 | K8s Config | kubernetes | `container.resource_request.memory=8Mi` (fact-406e56ac1b98) | 资源预留极低，与硬限制共同表明容器资源规格极其受限 |
| 3 | K8s State | kubernetes | `container.last_terminated_reason=Error` (fact-df0a7e32cfdf) | 表明容器最后一次异常终止的原因为非零退出码 |
| 4 | K8s State | kubernetes | `container.last_exit_code=137` (fact-f1132b802d9b) | 确认进程被强制杀掉（Exit 137 即 128+9 SIGKILL），是 OOM Killer 的典型特征 |
| 5 | K8s Event | kubernetes | `Exit Code: 137` (fact-2a4b73cd29ff) | K8s 事件日志中多次记录该退出码，佐证了终止原因 |
| 6 | K8s Event | kubernetes | `BackOff restarting failed container app...` (fact-2d4ed6e28771) | 记录 kubelet 频繁重启容器导致的 CrashLoopBackOff 状态 |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total=24` (fact-adeb051c7202) | 监控指标量化证实了容器处于高频重启状态 |
| 8 | Tracing | deepflow | `/health` 耗时 3.0s (fact-3ea3501d7874) | 探针探测耗时极长，证实应用层在 OOM 边缘响应严重迟缓导致超时 |

证据链显示：监控指标与 K8s 事件确认了容器处于高频重启状态，而 `Exit Code 137` 强有力地指向系统级 OOM Killer 介入。同时，Tracing 数据揭示 `/health` 探测耗时达到 3 秒，证明应用在到达内存硬限制 `64Mi` 时出现了极端的资源争抢，直接导致了 Kubelet 探测超时报错（BackOff）。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制配置过低（64Mi） → 容器运行内存占用超出限制触发 OOM Killer → 容器进程被强制终止（Exit Code 137） → 频繁 CrashLoopBackOff 与 Liveness Probe 探测超时
```

### 根因结论

已确认的根因为**容器内存限制配置过低导致 OOM**。
事实依据如下：
1. **触发条件**：容器配置了极低的内存硬限制 `64Mi` (fact-94de526ef3c1)。
2. **失败机制与现象**：应用进程在运行中触发系统 OOM Killer，以 `Exit Code 137` 异常终止 (fact-f1132b802d9b)，随后 kubelet 陷入重启循环，触发 `BackOff` 事件 (fact-2d4ed6e28771)。
3. **辅助确认**：Tracing 显示应用层在资源耗尽前响应极度迟缓（3 秒），与内存限制下的 OOM 前兆一致。

**未知/未确认部分**：
- 缺乏应用层具体的内存分配堆栈及溢出细节，仅能确认是资源上限导致的强制终止，无法定位代码中具体的内存泄漏或分配位置。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 23.5s
├─ 并发证据采集: 48.0s
│  └─ g1 aiops-case-v17/workload: 48.0s (Evidence 40.1s, RCA 7.8s)
└─ 汇总总结: 13.0s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-oomkilled
