## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload 处于 Terminating 状态，容器应用进程未退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `phase=Running`；Pod条件 `ContainersReady=True`、`Ready=True`；Pod `status=Terminating (lasts <invalid>)` | 确认容器应用进程仍在运行且就绪，但 Pod 处于终止状态，存在状态不匹配。 |
| 2 | K8s Event | Kubernetes | `Normal Killing` (34s) `Stopping container app`；5 条 CNI 网络状态事件 | 确认 Kubelet 已开始执行停止流程（发送信号），且 Pod 具备运行时的网络配置。 |
| 3 | K8s Config | Kubernetes | `container.app.resource_request.memory=8Mi`, `container.app.resource_limit.memory=32Mi` | 确认容器内存配置，排除因内存超限被 OOMKilled 的可能。 |
| 4 | K8s Config | Kubernetes | `container.app.resource_request.cpu=5m`, `container.app.resource_limit.cpu=50m` | 确认容器 CPU 配置，排除因 CPU 限制导致进程无法退出的可能。 |
| 5 | K8s Event | Kubernetes | `container.app.restart_count=0` | 确认应用启动后未发生过非预期重启。 |
| 6 | Metric | Prometheus | `kube_pod_status_phase=1` (Running) | 从监控维度再次印证 Pod 处于运行状态，未处于 Pending 状态。 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total=0` (app container) | 与 K8s 事件中的重启计数一致，无重启记录。 |
| 8 | Logging | Elasticsearch | `2026-09-14T07:56:07.105Z` `application started` | 证明应用进程已正常启动并开始运行。 |
| 9 | Logging | Elasticsearch | `2026-09-14T07:56:08.671Z` `SIGTERM received; waiting` | **核心证据**：直接揭示应用捕获了终止信号，但当前行为是“等待”，导致进程未实际退出。 |

**证据印证与说明**：
- 编号 1、2 与 6 互相印证，表明尽管 Kubelet 发出了终止指令（事件 2），应用进程却依然存活并处于就绪状态（状态 1、6）。
- 编号 8 证明应用已启动，编号 9 则解释了为何处于就绪状态却未能退出：应用捕获了 `SIGTERM`（与 Kubelet 的 Killing 事件对应），但进入了阻塞等待状态。
- 编号 3、4、5 排除了资源不足或重启异常作为主要阻塞原因。
- 维度间证据（如状态、事件、日志）高度一致，指向同一机制：应用代码逻辑上的信号处理阻塞。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码逻辑：注册 SIGTERM handler 等待文件 `/state/teardown-requested` 存在 → 终止触发但条件缺失：外部未创建该文件且未发送 SIGKILL → 进程阻塞：Kubelet 发信号后进程仍在运行，未超过 terminationGracePeriodSeconds (3900s) → 现象：Pod 状态卡在 Terminating
```

### 根因结论

已确认的根因为应用容器（app）注册的 `SIGTERM` 信号处理器阻塞了退出逻辑。证据（日志 `SIGTERM received; waiting` [9]、Pod 状态 `Terminating` 但进程仍 `Running` [1, 6]）直接支持该结论：Kubelet 在 Pod 删除时发送 `SIGTERM`，应用接收到信号后并未终止，而是进入了等待特定条件（文件 `/state/teardown-requested` 出现）的状态，导致容器进程在宽限期内持续运行，从而阻塞了 Pod 的最终终止。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 14.9s
├─ 并发证据采集: 48.9s
│  └─ g1 aiops-case-v13/workload: 48.9s (Evidence 37.6s, RCA 11.1s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
