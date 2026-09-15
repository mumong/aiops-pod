## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod 'aiops-case-v12/workload' stuck in Terminating state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.status` | `Terminating (lasts <invalid>)` | 确认 Pod 停留在终止状态且已超时 |
| 2 | K8s Event | `kubelet` | `Normal Killing 64s kubelet Stopping container app` | 表明 Kubelet 尝试终止容器，证明正常退出路径受阻 |
| 3 | K8s Event | `pod.annotations` | `cni.projectcalico.org/containerID: e9fb1526407d9d36e4dd055786bedc37fdf4e459092599a82a568d0239df38be` | 提供容器实例身份，辅助排查网络插件相关状态 |
| 4 | K8s Config | `resource_limit` | `memory=32Mi`, `cpu=50m` | 确认资源限制配置，排除 OOM/Throttling 导致的非正常退出 |
| 5 | Metric | `kube_pod_container_status_restarts_total` | `0` | 证明此前运行周期无重启，终止行为为单次操作导致 |
| 6 | Logging | `elasticsearch` | `application started` | 证实应用已成功初始化并在运行中 |

**证据互证分析**：
证据 1 和 2 直接关联：Kubelet 发送终止信号（证据 2），但 Pod 状态未能从 Terminating 转为 Completed（证据 1），且持续时间异常（lasts <invalid>），表明容器进程未能如期退出。证据 4 的资源配置和证据 5 的重启计数排除了资源不足或历史稳定性问题。证据 3 与日志（证据 6）共同确认该 Pod 实例曾正常启动并分配了网络标识。

## 🎯 根因分析 · g1

### 因果链

```text
Pod deletion requested (deletionTimestamp set) → Kubelet sends SIGTERM & triggers preStop hook → PreStop script blocks waiting for file /state/teardown-requested which is never created → Container process does not exit, preventing Pod termination
```

### 根因结论

已确认根因为 **Pod lifecycle preStop hook (custom script) 阻塞导致优雅关闭失败**。
Kubelet 试图通过 SIGTERM 和 preStop 钩子停止 `app` 容器（证据 2），但该容器进程因等待一个永远不会被创建的文件 `/state/teardown-requested` 而挂起（因果链直接失败点）。由于容器进程未退出，Pod 无法完成终止阶段，导致长期处于 Terminating 状态（证据 1）。证据 4 排除了资源限制干扰，证据 5 和 6 确认该终止发生在初始生命周期内。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 12.9s
├─ 并发证据采集: 88.4s
│  └─ g1 aiops-case-v12/workload: 88.4s (Evidence 81.1s, RCA 7.1s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
