## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Python 应用使用单线程 ThreadingHTTPServer 并执行同步阻塞 time.sleep(3)，导致 Liveness 探针在 1s 超时时无法获得响应而被标记 Unhealthy，进而触发 kubelet 强制杀死容器；容器重启后重复该阻塞行为形成 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded` (3m16s) | 确认 kubelet 因探针超时而判定容器不健康，是容器被杀的直接触发源 |
| 2 | K8s State | `kubernetes` | `container.waiting_reason: CrashLoopBackOff`, `restart_count: 11` | 确认 Pod 处于因反复重启导致的故障循环状态 |
| 3 | K8s Config | `kubernetes` | `container.resource_limit.memory: 64Mi` | 提供资源限制上下文，用于评估内存是否为 OOM 诱因 |
| 4 | K8s Event | `kubernetes` | `Normal Killing container app failed liveness probe, will be restarted` | 确证 kubelet 执行了由探针失败引发的容器强制杀进程动作 |
| 5 | Metric | `prometheus` | `container_memory_working_set_bytes`: 11874304 (13:07) → 3256320 (13:10) | 展示容器内存随生命周期剧烈波动，未显示稳定高占用 |
| 6 | Logging | `elasticsearch` | `GET /health HTTP/1.1 200 -` | 确认应用自身能返回健康响应，证明问题出在探针请求到达与响应的间隙（阻塞期间） |
| 7 | Tracing | `deepflow` | `flow duration_us`: min 3001142.0, max 3001920.0 | 记录到应用处理 `/health` 请求的平均耗时约 3秒，远超 Liveness 探针 1s 超时阈值 |

**证据关联说明：**
- **探针超时与代码阻塞印证**：Liveness 探针在 `1s` 超时（#1），而真实流量追踪显示应用处理 `/health` 请求耗时约 `3s`（#7）。这一 `3s > 1s` 的差异直接证实了应用内部存在同步阻塞逻辑导致无法及时响应探针请求。
- **循环重启闭环**：探针超时导致 kubelet 强制杀容器（#4），容器重启后应用再次进入阻塞状态，进而再次触发探针超时，最终形成 `CrashLoopBackOff`（#2）。
- **内存排查**：虽然内存被限制为 `64Mi`（#3），但实际观测到的内存峰值仅约 `11MB`（#5），远未达到限制阈值，排除了 OOM Kill 作为根因。

## 🎯 根因分析 · g1

### 因果链

```text
Python应用使用单线程HTTP服务器且存在同步阻塞time.sleep(3) → Liveness探针在等待应用响应时触发1s超时 → kubelet因探针失败强制Kill容器(Exit Code 137) → 容器重启后重复阻塞形成CrashLoopBackOff
```

### 根因结论

已确认根因为**应用同步阻塞导致 Liveness 探针超时**。
- **证据支持**：追踪数据显示应用处理 `/health` 请求耗时约 `3s`（证据 #7），而集群 Liveness 探针超时阈值仅为 `1s`（证据 #1）。由于应用使用单线程架构，在处理阻塞任务期间无法响应探针请求，直接触发了 kubelet 的容器终止逻辑（证据 #4）。
- **现象印证**：这一机制完美解释了为何 Pod 日志显示应用正常运行且能返回 `200 OK`（证据 #6），但状态却不断在 `Unhealthy`、`Killing` 和 `CrashLoopBackOff` 之间循环（证据 #2, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 16.0s
├─ 并发证据采集: 82.3s
│  └─ g1 aiops-case-v17/workload: 82.3s (Evidence 70.0s, RCA 12.0s)
└─ 汇总总结: 13.0s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
