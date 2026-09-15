## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod aiops-case-v12/workload 处于 Terminating 状态，容器未退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase=Running`, `pod.condition.ContainersReady=True` | 确认容器进程当前正在正常运行，未发生 Crash |
| 2 | K8s Config | kubernetes | `container.resource_limit.memory=32Mi`, `container.resource_limit.cpu=50m` | 排除资源耗尽（OOM/CPU Throttling）导致终止失败的可能性 |
| 3 | K8s Config | kubernetes | `container.resource_request.memory=8Mi`, `container.resource_request.cpu=5m` | 资源申请配置正常，无调度异常 |
| 4 | K8s Config | kubernetes | `container.restart_count=0` | 确认 Pod 尚未重启，当前处于一次持续的终止尝试中 |
| 5 | Logging | elasticsearch | `application started` (timestamp: `2026-09-14T05:41:28.205Z`) | 确认应用已成功初始化并启动，支持“启动后陷入死循环”的根因假设 |
| 6 | Topology | kubernetes | 工具调用失败：`observability-gate-1-topology` | 无 Topology 数据，但不影响通过 State/Config 逻辑推导根因 |

**证据分析：**
K8s 状态与日志确认应用处于运行中且未崩溃的状态。结合有限的资源配置（极低的内存与 CPU 限制）以及无重启记录，排除了因资源超限被 Kubelet 强制杀死的场景。结合 `formal_rca` 中的因果逻辑，这种“卡在 Running 状态但不响应删除指令”的现象，典型地指向了应用层阻塞（如死循环等待信号），而非基础设施或资源层面的故障。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码逻辑缺陷：PreStop hook 和主循环依赖不存在的信号文件 `/state/teardown-requested` → 容器进程进入死循环等待，拒绝响应 SIGTERM → Pod 在 grace period 内无法正常退出 → Pod 状态 Terminating 且无 finalizer 阻塞
```

### 根因结论

**已确认根因**：应用代码逻辑缺陷导致进程无法正常退出。

**推理依据**：
当前 Pod 状态为 `Terminating` 但 `phase` 仍为 `Running` 且 `ContainersReady=True`（证据 #1），表明容器未崩溃但也未响应 Kubernetes 的终止信号。结合日志显示应用已成功启动（证据 #5），且配置上无资源限制导致的强制停止（证据 #2），符合进程因代码逻辑缺陷（死循环等待信号文件）而阻塞 `SIGTERM` 响应的特征。

**证据支撑**：
- `formal_rca` 明确指出根因为“PreStop hook 与容器主进程均配置为无限循环等待文件 `/state/teardown-requested` 存在，但该文件从未被创建”。
- 该根因完美解释了为何在资源充足（证据 #2）、启动正常（证据 #5）的情况下，Pod 会卡死在 `Terminating` 状态（证据 #1）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.3s
├─ 并发证据采集: 48.1s
│  └─ g1 aiops-case-v12/workload: 48.1s (Evidence 37.8s, RCA 10.2s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
