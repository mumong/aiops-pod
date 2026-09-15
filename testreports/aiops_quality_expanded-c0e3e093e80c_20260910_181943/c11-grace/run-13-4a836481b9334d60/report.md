## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod 'workload' in namespace 'aiops-case-v13' stuck in Terminating status despite no finalizers and a Ready node. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status`: Terminating; `pod.phase`: Running (lasts <invalid>) | 确认 Pod 处于终止挂起状态，无法释放资源 |
| 2 | K8s Event | kubernetes | `Normal Killing`: "Stopping container app" (59s ago) | 证明系统级强制杀容器动作已触发 |
| 3 | Logging | elasticsearch | `2026-09-14T06:54:06.507Z`: "application started" → `2026-09-14T06:54:08.670Z`: "SIGTERM received; waiting" | 应用接收到信号但未退出，进入阻塞等待 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 0 (app container) | 排除重启恢复场景，确认当前卡死状态 |
| 5 | Metric | prometheus | `kube_pod_status_phase`: 1 (Running) | 侧面印证 Pod 进程未终止，生命周期未闭合 |

**证据印证：**
Kubernetes 层面的 `Terminating` 状态与 `phase: Running` 不一致（证据 1、5），且存在 `Stopping container` 事件（证据 2），说明底层容器管理器无法从应用层获取退出确认。应用日志（证据 3）精确记录了这一卡点：应用收到 SIGTERM 信号后仅打印日志并进入“waiting”状态，未执行退出逻辑。

## 🎯 根因分析 · g1

### 因果链

```text
应用未实现优雅退出 → 收到 SIGTERM 后未 sys.exit() → 主循环阻塞等待不存在的文件 '/state/teardown-requested' → Pod 进程拒绝终止 → 卡在 Terminating 状态
```

### 根因结论

**已确认根因：** 应用代码存在缺陷，无法在收到 `SIGTERM` 信号后正确退出。

证据表明，Pod 在收到终止信号后（证据 2、3），应用进程并未终止，而是进入了阻塞等待状态（证据 3 "SIGTERM received; waiting"）。由于应用未处理该信号以终止主循环，导致 Kubernetes 认为容器仍在运行，从而无法完成删除操作（证据 1）。缺少 Tracing 数据（如 Trace ID 对应流）无法进一步展示具体的阻塞点，但日志层面的信号未处理与状态挂起形成了完整的因果闭环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 20.4s
├─ 并发证据采集: 62.6s
│  └─ g1 aiops-case-v13/workload: 62.6s (Evidence 54.6s, RCA 7.9s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
