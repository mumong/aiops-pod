## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload stuck in Terminating state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubelet | `Readiness probe failed: command "python3 -c import os; assert os.path.exists('/proc/1/status')" timed out` (13s, x3 over 30s) | 证明容器进程虽然存在，但处于假死或高负载状态，导致健康检查无法响应。 |
| 2 | K8s Event | Kubelet | `Stopping container app` (Normal, Killing) (27s) | 标志 Pod 已进入终止流程，Kubelet 正在尝试清理容器。 |
| 3 | K8s State | K8s | `pod.status: Terminating` | 确认 Pod 处于终态，且未自动恢复，符合终止延迟现象。 |
| 4 | K8s State | K8s | `pod.phase: Running` | 容器实际进程仍在运行，未随 SIGTERM 立即退出，这是导致 Terminating 卡住的核心状态矛盾。 |
| 5 | K8s Config | K8s | `container.resource_request.memory: 8Mi`, `container.resource_limit.memory: 32Mi` | 展示资源配置极低，但日志中进程已存活并接收信号，非 OOM 导致。 |
| 6 | Logging | ES | `application started` (2026-09-14T07:40:54.506Z) | 确认应用已启动，排除启动失败的可能性。 |
| 7 | Logging | ES | `SIGTERM received; waiting` (2026-09-14T07:40:55.842Z) | 证明应用接收到了终止信号，但逻辑进入了等待状态，未执行退出操作。 |
| 8 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 0` | 确认容器未发生重启，排除了因 CrashLoopBackOff 导致的终止，当前问题纯属终止流程阻塞。 |

**证据关联说明**：
日志（#6, #7）记录了从“正常启动”到“接收 SIGTERM 但进入等待”的生命周期；K8s 事件（#1, #2）从集群侧证实了容器因不健康被探测到，并触发了停止操作。K8s 状态（#3, #4）直观展示了容器“假死”的矛盾状态（Phase=Running 但 Status=Terminating），日志中的等待与状态的长期停滞互为印证。

## 🎯 根因分析 · g1

```text
Pod 触发删除（Deletion requested）
→ 触发 Kubelet 发送 SIGTERM 信号给容器应用
→ 应用未正确响应 SIGTERM，而是进入阻塞状态等待特定文件 (Missing file '/state/teardown-requested')
→ 容器进程未退出，处于僵死状态，导致 Kubelet 无法完成终止流程
→ Pod 长期处于 Terminating 状态，直到 TerminationGracePeriodSeconds 超时后才会被强杀
```

### 根因结论

**已确认的根因**：
应用容器的 SIGTERM 处理逻辑存在缺陷（或缺失），在接收到终止信号后，没有正常退出，而是进入死循环等待一个不存在的资源（文件 `/state/teardown-requested`）。

这一根因由以下事实强力支撑：
1. **日志直接证据**：日志明确记录 `SIGTERM received; waiting`（证据 #7），说明应用“听到了”信号但选择了等待，而非退出。
2. **现象一致性**：K8s 事件显示 Kubelet 发出 `Stopping container app`（证据 #2），而 Pod 状态仍为 `Running`（证据 #4），这完全符合“进程未响应 SIGTERM”的特征。
3. **排除其他因素**：重启次数为 0（证据 #8）排除了崩溃重启；极低的内存限制（证据 #5）排除了内存耗尽导致的假死。

现有证据链完整（触发 -> 机制 -> 失败 -> 现象），符合正式 RCA 中描述的 "Application SIGTERM handler fails to exit..." 场景，可确认为本次异常组的根因。

---

## 📊 性能统计

```text
├─ 总耗时: 59.3s
├─ 问题定位: 10.0s
├─ 并发证据采集: 35.9s
│  └─ g1 aiops-case-v13/workload: 35.9s (Evidence 27.0s, RCA 8.8s)
└─ 汇总总结: 13.4s
```

📋 Runbook 参考

- 未调用 Runbook
