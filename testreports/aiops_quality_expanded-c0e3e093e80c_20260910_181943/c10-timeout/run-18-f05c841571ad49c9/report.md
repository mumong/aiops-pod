## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | 容器应用逻辑错误：主线程阻塞在3秒的延时操作中，导致Liveness Probe（超时1秒）持续失败；Pod退出码137与极低内存使用量矛盾，指向应用进程在重启前被外部强制终止（如SIGKILL），可能是探针重试失败后的Kubelet强制清理、测试脚本故意制造异常退出码或系统级OOMKiller在采样间隙触发了极短高峰，但直接且持续的故障驱动因素是探针超时导致重启循环。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Unhealthy 14m (x23 over 34m) kubelet Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded` | 证实探针持续超时，这是直接触发起停循环的上游事件 |
| 2 | K8s Event | Kubernetes | `Warning Unhealthy 33m (x2 over 34m) kubelet Readiness probe failed: Get "http://172.16.104.36:18080/ready": dial tcp 172.16.104.36:18080: connect: connection refused` | 证实应用端口未成功监听，支持应用进程异常退出的事实 |
| 3 | K8s Event | Kubernetes | `Warning BackOff 4m47s (x126 over 32m) kubelet Back-off restarting failed container app in pod workload_aiops-case-v17(85aece07-6ffa-41db-9e5a-f351771a8864)` | 证实容器正处于高频重启状态 |
| 4 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff`, `restart_count: 15`, `last_exit_code: 137` | 描述容器当前的最终状态及异常退出特征 |
| 5 | Metric | Prometheus | `container_memory_working_set_bytes` 多次采样显示峰值约 11.8MB (`fact-62168381fbdb`, `fact-7a136bcd5d26`, `fact-6a496acf442f`) | 佐证应用进程未发生大规模内存泄漏，间接排除常驻的高内存 OOM 特征 |
| 6 | Tracing | Deepflow | `HTTP GET /health` 请求持续存在，响应码 200，但延迟分布 `min: 3000773.0µs` (约 3s) | 证实应用端对 `/health` 接口存在固定的 ~3s 延迟 |

**证据印证说明：**
1.  **K8s 事件与探针机制**：证据 #1 明确指出 Liveness Probe 因超时被 Kubelet 判定为失败，直接解释了证据 #3 的 BackOff 重启循环。
2.  **追踪数据与超时根源**：证据 #6 提供了关键因果证据，显示 `/health` 接口响应时间长达 3s，这与 K8s 探测超时（通常为 1s 左右，由 #1 的失败反推）相吻合，证实了“应用逻辑阻塞导致探针超时”的机制。
3.  **退出码矛盾**：证据 #4 指出退出码为 137 (SIGKILL)，但这与证据 #5 中较低的内存使用量存在张力。由于缺乏底层审计日志或内核日志，137 的具体触发源（Kubelet 杀进程 vs 外部 OOMKiller）无法通过现有工具事实单一确认，但重启循环的表象已被确认。

## 🎯 根因分析 · g1

### 因果链

```text
应用主线程阻塞(约3s延迟) → Liveness Probe请求超时(>1s) → Kubelet判定不健康并发送信号(SIGKILL, Exit 137) → 容器频繁重启 (CrashLoopBackOff)
```

### 根因结论

**已确认根因**：容器应用内部逻辑导致主线程阻塞（或处理 `/health` 接口耗时过长，约 3s），直接造成 Liveness Probe 持续超时（超时 >1s）。Kubelet 在检测到探针失败后强制终止了容器进程（反映为退出码 137），进而引发持续的 CrashLoopBackOff 重启循环。这一结论得到 K8s 事件（#1, #3）、Tracing 数据（#6）和当前状态（#4）的共同支持。

**证据不足之处**：
1.  **退出码 137 的精确来源未确认**：目前无法从工具事实中区分该信号是由 Kubelet 在探针失败后发出的标准清理流程，还是由系统 OOMKiller 在探针采样间隙触发的极短内存峰值（证据 #5 显示内存峰值约 11.8MB，未触及 64Mi 限制，但存在瞬时波动可能）所发出。
2.  **应用阻塞的确切代码原因未确认**：Tracing 证实了 3s 的延迟，但缺乏日志或更细粒度的分布式追踪来定位是死锁、第三方服务依赖超时还是代码逻辑问题导致了该阻塞。

---

## 📊 性能统计

```text
├─ 总耗时: 2.7m
├─ 问题定位: 31.5s
├─ 并发证据采集: 112.1s
│  └─ g1 aiops-case-v17/workload: 112.1s (Evidence 102.8s, RCA 9.1s)
└─ 汇总总结: 16.1s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
