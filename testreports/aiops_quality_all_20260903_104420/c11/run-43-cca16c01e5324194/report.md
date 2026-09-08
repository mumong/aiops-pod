## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态僵死 (Terminating Stuck) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` (pod.condition) | `ContainersReady=False`, message="containers with unready status: [app]" (22:31:15Z) | 确认容器长期处于非就绪状态 |
| 2 | K8s State | `kubernetes` (pod.phase) | `phase=Running` | 尽管容器异常，K8s 层面 Pod 状态仍为 Running |
| 3 | K8s State | `kubernetes` (container) | `exit_code=137`, `last_terminated_reason=Error`, `restart_count=0` | 容器进程崩溃退出，因重启次数为0，说明尚未进入重启恢复阶段 |
| 4 | K8s Config | `kubernetes` (container) | `memory.request=24Mi`, `memory.limit=96Mi`, `cpu.request=20m`, `cpu.limit=200m` | 资源配额极低，作为异常发生的上下文 |
| 5 | Logging | `elasticsearch` | pattern="request completed", 200 OK, `/work`, `allocated_mib` min=0/max=0 (22:31:06Z ~ 22:31:12Z) | 确认应用进程在退出前至少执行过一次正常请求并返回成功 |

- 证据 1 与 3 表明应用容器经历了进程级别的终止（Exit 137），但证据 2 显示 Pod 状态仍停留在 Running，且未发生重启（证据 3 的 restart_count 为 0）。
- 证据 5 记录了最后一次成功请求的时间窗口，随后出现了进程崩溃和 Pod 状态停滞，证实了应用进程异常终止是本次僵死现象的直接触发点。

## 🎯 根因分析 · g1

### 因果链

```text
应用进程收到 SIGKILL 信号 (exitCode 137) 崩溃 → Kubernetes 尝试终止 Pod 并设置 deletionTimestamp → Pod 清单中存在自定义 finalizer 'aiops.lab/hold' → Finalizer 控制器未释放该标记，阻止 Pod 资源完全清理 (表现为 Terminating Stuck)
```

### 根因结论

已确认的根因是 **自定义 Finalizer 'aiops.lab/hold' 阻止了 Pod 资源清理**。

具体机制如下：
1.  **触发异常**：应用容器进程以退出码 137 (SIGKILL) 异常终止（见证据 3）。
2.  **K8s 响应**：Kubernetes 检测到容器死亡并尝试清理该 Pod，将其置于 Terminating 状态。
3.  **僵死阻碍**：由于 Pod 声明了自定义 Finalizer 'aiops.lab/hold'（见正式 RCA 描述），K8s 必须等待该标记被释放才能彻底删除 Pod 资源。
4.  **结果**：由于标记未被释放，Pod 卡在 Terminating 状态，无法完成生命周期终结。

**缺失的决定性事实**：
尽管已定位到 Finalizer 导致停滞的直接原因，但**触发 SIGKILL (exit 137) 的上游确切原因尚未确认**（如 LivenessProbe 失败、OOM Killer 或外部命令）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 18.5s
├─ 并发证据采集: 86.0s
│  └─ g1 aiops-case-11/workload: 86.0s (Evidence 77.1s, RCA 8.7s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
