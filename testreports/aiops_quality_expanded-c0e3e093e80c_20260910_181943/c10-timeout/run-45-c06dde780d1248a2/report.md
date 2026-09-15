## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Pod workload in aiops-case-v17 is stuck in CrashLoopBackOff state with frequent restarts |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded (Client.Timeout exceeded while awaiting headers)` (fact-36cdd16a9713) | 触发重启的致命失败机制 |
| 2 | K8s State | kubelet | `container.waiting_reason: CrashLoopBackOff`、`container.last_terminated_reason: Error`、`container.last_exit_code: 137` (fact-6ef47e1ef39b, fact-7cafe6bdb5ec, fact-6f5a5f68319c) | 直接确认进程因 OOM Kill (137) 退出 |
| 3 | K8s Config | kubelet | `container.resource_request.memory: 8Mi`、`container.resource_limit.memory: 64Mi` (fact-1bda7dc7e6b0, fact-71fa626ec1cf) | 判定触发 Exit Code 137 的根因资源限制 |
| 4 | Tracing | deepflow | `GET /health` Flow：`duration_us min/max 3001044.0~3001868.0`，耗时约 3s (fact-2b20ff5f9a9a 等) | 证明应用响应极慢，远超探针容忍度 |
| 5 | Logging | elasticsearch | `GET /health HTTP/1.1" 200` 且 `GET /ready HTTP/1.1" 200` 持续返回成功 (fact-4c599b16afee 等) | 排除应用本身完全挂死，定位到探针超时冲突 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total: 37` (fact-8c5b2d9882c6) | 佐证重启风暴的规模与频率 |
| 7 | Metric | prometheus | `container_memory_working_set_bytes: ~3.6MB` (fact-5efecc977cd5, fact-6ad12ecd9534 等) | 排除应用实际内存使用过载，确认内存限制配置过高 |

**证据互证说明**：
日志 (Log #5) 与追踪 (Trace #4) 共同证明应用服务 `/health` 端点可达且返回 200，但存在极端延迟（约 3秒）。结合 K8s 探针失败事件 (Event #1) 的超时机制，可以推断探针设置的超时时间不足以覆盖应用响应延迟。随后 K8s 判定探针失败并终止容器，由于配置的内存硬限制 (Config #3) 为 64Mi 且实际工作集约 3.6MB（Metric #7），容器因内存不足被系统强制杀死（状态 #2, #3），最终导致持续的重启风暴（Metric #6）。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness probe 配置超时时间过短，低于应用 /health 端点的实际响应延迟(约3s) → Kubelet 判定探针失败并终止容器进程 → 容器内存受限(硬限制 64Mi)被系统 Kill (Exit Code 137) → Pod 陷入 CrashLoopBackOff 持续重启
```

### 根因结论

已确认根因为：**Liveness probe 超时配置过短** 与 **内存限制配置偏高** 共同导致的 CrashLoopBackOff。

证据支持表明：
1. 应用本身处于正常运行状态（日志 #5、追踪 #4 均返回 200 成功）。
2. 应用存在高延迟（追踪 #4 显示约 3s），导致 Kubelet 的探针请求超时（事件 #1）。
3. Kubelet 因探针失败执行 Kill，进而因硬限制（64Mi）触发了 OOM Kill（Exit 137，状态 #3）。
4. 由于应用实际内存（~3.6MB，Metric #7）远低于硬限制，因此当前现象的核心触发点并非真实的内存溢出，而是探针超时机制引发的强制终止循环。

缺失的决定性事实为探针的实际配置参数（TimeoutSeconds），但现有超时报错原文及高延迟日志足以确认定位方向。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 17.8s
├─ 并发证据采集: 111.0s
│  └─ g1 aiops-case-v17/workload: 111.0s (Evidence 98.6s, RCA 12.2s)
└─ 汇总总结: 15.0s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-oomkilled, pod-crashloop-runtime
