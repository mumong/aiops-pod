## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod workload in Terminating state (describe) / Running (yaml) for ~69s with preStop hook waiting |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status`: Terminating (lasts <invalid>); `pod.phase`: Running | 直接确认 Pod 处于无法退出的 Terminating 阶段 |
| 2 | K8s Event | kubernetes | `Killing` (69s): "Stopping container app" | 验证 kubelet 已在 69 秒前发起容器停止指令 |
| 3 | Metric | prometheus | `restart_count` = 0 (2026-09-11T17:56:45.621000Z) | 确认容器在异常期间未发生重启，非崩溃重启问题 |
| 4 | Logging | elasticsearch | "application started" (2026-09-11T17:55:48.103Z) | 提供时间参考点，确认应用启动后至今运行正常 |

当前集群内唯一的异常表现是 `aiops-case-v12/workload` 所在的 Pod 在发起删除请求 69 秒后仍停留在 `Terminating` 状态。Kubernetes 状态（证据 1）与事件（证据 2）证实删除指令已下发且容器停止流程已启动。Metric 监控（证据 3）显示重启计数为 0，排除了因容器频繁崩溃导致删除受阻的可能性，结合日志（证据 4）的无异常输出，可推断该 Pod 正处于正常的、由特定条件触发的优雅退出阻塞中。

## 🎯 根因分析 · g1

### 因果链

```text
Deletion requested (deletionTimestamp set) → preStop hook starts waiting for /state/teardown-requested → File not yet present, hook looping (time.monotonic < deadline) → Pod remains in Terminating state until preStop exits or grace period expires
```

### 根因结论

已确认的根因是：Pod 的 `preStop` hook 正在等待特定条件（文件 `/state/teardown-requested` 出现），在该条件未满足前，容器无法退出，从而导致 Pod 长期处于 `Terminating` 状态。

具体依据如下：
- **现象与机制确认**：Pod 已进入 `Terminating` 状态（证据 1），且 kubelet 正在执行停止操作（证据 2）。Metric 数据（证据 3）确认容器未重启，说明容器仍在运行但无法正常退出，符合 `preStop` 阻塞退出的特征。
- **缺失的决定性事实**：正式 RCA 指出无法确认 `/state/teardown-requested` 文件是否存在或即将被外部控制器创建。由于缺少这一关键状态证据，目前的诊断停留在“机制阻塞”层面，无法进一步确认该等待是预期的长时同步过程，还是外部控制器未能正确触发预期行为。因此，当前证据不足以断定是否存在需要人工干预的系统故障。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.4s
├─ 并发证据采集: 37.1s
│  └─ g1 aiops-case-v12/workload: 37.1s (Evidence 27.1s, RCA 9.9s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
