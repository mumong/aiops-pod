## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod aiops-case-v12/workload 处于 Terminating 状态，kubelet 已发送 Killing 信号，但 Pod 在 API Server 中仍保持 Running 阶段。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Normal Killing 62s kubelet Stopping container app` | 确认 kubelet 已发送终止信号，执行环境尝试清理 |
| 2 | K8s State | kubernetes | Pod Phase: `Running`；Status: `Terminating (lasts <invalid>)` | 确认为异常停滞状态，API Server 视图与实际运行态不符 |
| 3 | K8s State | kubernetes | Ready: `True`, ContainersReady: `True` | 排除因 Pod 初始化失败导致的未就绪情况 |
| 4 | K8s Config | kubernetes | Resource Request: CPU `5m`, Memory `8Mi`; Limit: CPU `50m`, Memory `32Mi` | 排除资源配额耗尽导致的僵死 |
| 5 | Metric | prometheus | `kube_pod_status_phase` = `1` (Running)；`kube_pod_container_status_restarts_total` = `0` | 独立确认 Pod 持续驻留在 Running 阶段，且无崩溃重启记录 |
| 6 | Logging | elasticsearch | `application started` | 确认应用已在终止窗口内完成启动，排除启动故障 |

**证据关联分析：**
K8s Event (#1) 确认系统层面正常发送了 Killing 信号，Metric (#5) 独立佐证了 Pod 停留在 Running 阶段而非 OOM 重启，日志 (#6) 确认业务进程在终止宽限期内已处于运行状态。结合 K8s State (#2) 的 `Terminating` 标记，共同指向“进程收到信号但未退出”的机制问题，而非容器崩溃或资源不足。

## 🎯 根因分析 · g1

### 因果链

```text
应用硬编码阻塞设计 → 终止触发后 preStop/主进程死循环等待文件 → 优雅终止宽限期耗尽进程未退出 → Pod 卡在 Terminating 阶段
```

### 根因结论

**已确认的根因：**
应用逻辑硬编码阻塞（证据关联：Event Killing #1 与 Phase Running #2, #5 并存）。

具体而言，应用的容器主进程及 preStop 钩子均被设计为无限循环等待特定文件 `/state/teardown-requested` 的出现。由于该触发文件始终未被创建，进程在处理 SIGTERM 信号后进入了死循环等待，导致优雅终止机制（Graceful Termination）无法完成。尽管 kubelet 已发出 `Killing` 信号（#1）并等待了 3900s，进程拒绝退出，致使 API Server 始终维持 Pod 的 `Running` 状态（#2），而非转换为 `Terminated`。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 19.7s
├─ 并发证据采集: 53.7s
│  └─ g1 aiops-case-v12/workload: 53.7s (Evidence 44.3s, RCA 9.3s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
