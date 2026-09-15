## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | {'type': 'Initialized', 'status': 'True'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-v12/workload` 状态: `Terminating` (lasts <invalid>), 相位: `Running` | 定义现象：Pod 处于终止阶段但未完全退出，状态停滞 |
| 2 | K8s Event | kubernetes | `Normal Killing 53s kubelet Stopping container app` | 证明 Kubelet 已发起终止动作，但容器尚未进入 Terminated 状态 |
| 3 | K8s Config | kubernetes | 容器资源限制: Memory `32Mi`, CPU `50m` | 排除资源硬限制导致进程因 OOM/Throttling 异常退出的可能性 |
| 4 | K8s Config | kubernetes | 容器重启次数: 0 | 排除因容器反复崩溃重启导致的异常 |
| 5 | Logging | elasticsearch | 日志消息: `application started` | 确认应用进程已启动，但未观察到与终止（teardown/prestop）相关的日志 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total` = 0 | 佐证容器自启动以来未发生过重启事件 |

证据互证说明：
- K8s 状态（#1）确认了 Pod 处于停滞的 `Terminating` 状态，事件（#2）证实了 Kubelet 的终止尝试已发生，但容器状态仍为 `Running`，二者结合排除了“未收到删除请求”的情况，指向**进程主动拒绝终止或阻塞**。
- 资源配置（#3）与日志（#5）显示应用处于正常启动状态且受限于特定资源配额，无资源过载迹象，排除了资源耗尽导致的死锁。
- 日志（#5）仅记录了启动信息，缺失任何关于 `prestop` 或 `teardown-requested` 的记录，与 K8s 事件（#2）的“正在停止”动作形成断层，暗示应用可能在等待某个外部条件或钩子未完成。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 接收删除请求并进入 Terminating 阶段 → Kubelet 发送 Stopping 信号 → 容器进程未响应（或阻塞） → 用户可见 Pod 状态为 Terminating 且持续
```
*注：具体的阻塞机制（如 PreStop Hook 或应用内部逻辑）因缺乏日志证据，标记为“未确认”。*

### 根因结论

**证据不足。**

目前证据（K8s State, Event, Logging, Metric）仅能证明 Pod 在 Kubelet 发起 `Stopping container` 动作后，未能从 `Running` 转入 `Terminated` 状态，表现为停滞。然而，由于缺乏容器内的具体执行上下文，无法确定导致停滞的确切原因：
1. 无法确认 `PreStop Hook` 是否启动或是否执行超时。
2. 无法确认应用进程是否正在等待特定的文件信号（如 `/state/teardown-requested`）或外部消息。
3. 无法区分该状态是正常的“宽限期等待”还是异常的“死锁”。

决定性事实缺失：应用进程内部在接收到终止信号后的行为日志，或 `prestop` hook 的执行状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 18.6s
├─ 并发证据采集: 63.0s
│  └─ g1 aiops-case-v12/workload: 63.0s (Evidence 50.7s, RCA 12.2s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
