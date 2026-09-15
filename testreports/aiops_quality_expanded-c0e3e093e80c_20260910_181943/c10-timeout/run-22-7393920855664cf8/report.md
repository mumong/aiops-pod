## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Pod容器app的内存资源限制（memory limit 64Mi）过低，Python进程启动后无法在受限内存下持续运行，导致被Linux OOM Killer反复终止（Exit Code 137），进而触发CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | `fact-0ae064aa882c` | memory limit: `64Mi` | 定义关键限制值，构成故障上下文 |
| 2 | K8s State | `fact-1e88e9178220` | exit_code: `137` | 直接证明进程遭遇强制杀终止（OOM Killer） |
| 3 | K8s State | `fact-5d800d108bf6` | container.last_terminated_reason: `Error` | 确认容器异常退出的直接原因 |
| 4 | K8s Event | `fact-fb1c0026b092` / `fact-2225ce9a1dbf` | 事件 `Killing` 及日志 `Exit Code: 137` | 记录 kubelet 因 Liveness Probe 失败触发杀除动作 |
| 5 | K8s State | `fact-c7bb748bdbd3` | waiting_reason: `CrashLoopBackOff` | 描述最终的异常状态结果 |
| 6 | Metric | `fact-ab841e28e19a` | restart_count: `21` | 证实 CrashLoopBackOff 模式正在持续发生 |
| 7 | Metric | `fact-eaf7075d8b47` | waiting_reason: `CrashLoopBackOff` | 独立验证集群状态与 K8s 事件一致性 |
| 8 | Logging | `fact-2f8a2521c8d6` | `listening on 18080` | 记录进程启动并暴露端口的行为，与退出原因无关 |
| 9 | Tracing | `fact-33fd71452ae6` (聚合) | GET /health -> 200, 耗时约 3s | 确认探针本身逻辑成功，排除应用服务无响应导致的误杀 |

**证据链说明：**
Kubernetes 层面，`64Mi` 的内存限制（证据 1）与容器异常退出代码 `137`（证据 2）结合，直接指向 Linux OOM Killer 机制。由于 OOM 触发，Liveness Probe 检查失败，导致 kubelet 执行杀除动作（证据 4）。日志显示服务确实在监听（证据 8），且追踪流量确认探测协议响应正常（证据 9），排除了服务假死的可能，进一步确认杀除是由资源耗尽导致的进程终止所致。Metric 数据（证据 6、7）在独立系统中印证了该 CrashLoopBackOff 现象的持续性和严重性。

## 🎯 根因分析 · g1

### 因果链

```text
64Mi 内存限制过低（证据 1）→ Python 进程启动/运行触发 OOM Killer → 进程被杀 (Exit Code 137, 证据 2, 3) → Liveness Probe 失败触发杀除并重启 → CrashLoopBackOff (证据 4, 5)
```

### 根因结论

**已确认的根因**是：Pod 容器 `app` 的内存资源限制配置过低。

具体而言，容器 `app` 被硬性限制了 `64Mi` 内存（证据 1），该资源不足以支持 Python 进程的正常稳定运行。Python 进程在运行期间因内存耗尽被 Linux OOM Killer 强制终止（证据 2），退出码为 `137`（证据 2, 3）。这一终止行为导致了 Liveness Probe 失败，kubelet 进而触发重启策略，最终使得 Pod 进入 `CrashLoopBackOff` 状态（证据 4, 5）。Metric 数据证实该异常循环已导致 21 次重启（证据 6），且应用本身服务无响应假象（证据 8, 9），进一步排除了其他代码逻辑故障的可能。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 27.3s
├─ 并发证据采集: 84.8s
│  └─ g1 aiops-case-v17/workload: 84.8s (Evidence 77.2s, RCA 7.4s)
└─ 汇总总结: 13.3s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
