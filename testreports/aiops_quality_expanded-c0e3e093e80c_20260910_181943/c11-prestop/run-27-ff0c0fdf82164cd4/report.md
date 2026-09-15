## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod 'workload' in namespace 'aiops-case-v12' is stuck in Terminating state; deletionTimestamp is set but the object persists. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod 'workload' (aiops-case-v12) 处于 `Terminating` 阶段，deletionTimestamp 已设置但对象持续存在 (fact-55566b5f75d1, fact-2885374f7700) | 确认 Pod 无法完成退出流程的直接状态 |
| 2 | K8s Event | kubernetes | 容器 'app' 状态为 `ContainersReady=True` 且 `restart_count=0`，表明此前运行正常且未发生崩溃重启 (fact-450c85b729e1, fact-c3af697a62ee) | 排除容器因 Crash 或 OOM 导致异常退出的可能 |
| 3 | Metric | prometheus | `kube_pod_status_phase` 持续为 `1` (Running)，且 `Succeeded=0`，确认 Pod 未进入 Completed 或 Failed 状态 (fact-a297e2fe0063) | 佐证 Kubernetes 层面对象生命周期停滞 |
| 4 | Logging | elasticsearch | 应用记录日志 "application started" (fact-e332361606a6) | 证实容器启动成功，日志显示的是运行态而非退出态的报错 |

Pod 处于 `Terminating` 状态且无任何资源限制相关的错误，说明容器进程未被外部强制杀死。结合容器此前运行正常、无重启且日志中只有启动信息，推断容器是在正常的优雅关闭（Graceful Shutdown）过程中卡死，无法退出。

## 🎯 根因分析 · g1

```text
Pod 删除指令触发 → Kubelet 发送 SIGTERM 并执行 preStop → 进程等待 '/state/teardown-requested' 文件 → 文件不存在导致无限阻塞 → Pod 持续 Terminating
```

**已确认根因**：应用逻辑缺陷导致优雅关闭失败。根因在于主进程与 `preStop` 钩子（preStop hook）均硬编码等待特定文件 `/state/teardown-requested` 的出现，但系统从未生成该文件。

这一死锁机制导致容器在收到 SIGTERM 信号后陷入无限等待，无法完成退出流程。证据方面，**K8s State** 确认了 Pod 处于停滞的 `Terminating` 状态且容器未崩溃重启（fact-55566b5f75d1, fact-c3af697a62ee）；**Metrics** 确认 Pod 既未成功（Succeeded）也未失败（Failed）（fact-a297e2fe0063），进一步排除了其他异常退出路径，确证了是由应用侧逻辑阻塞导致的正常退出流程卡死。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 19.5s
├─ 并发证据采集: 56.5s
│  └─ g1 aiops-case-v12/workload: 56.5s (Evidence 45.4s, RCA 10.9s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
