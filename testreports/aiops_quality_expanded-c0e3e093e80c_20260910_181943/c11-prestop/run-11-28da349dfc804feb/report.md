## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | {'type': 'PodScheduled', 'status': 'True'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase`: Running, `container.restart_count`: 0 | 确定异常实体为 pod `aiops-case-v12/workload`，且无重启行为。 |
| 2 | K8s Event | kubernetes | `pod.condition` 状态包括 `PodScheduled: True`, `Initialized: True`, `ContainersReady: True`, `Ready: True` | 证明容器启动成功并健康运行过，非启动类故障，而是运行中或终止时的卡滞。 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory`: 32Mi, `container.resource_limit.cpu`: 50m | 提供容器资源边界上下文，排除内存溢出导致的崩溃重启。 |
| 4 | Logging | elasticsearch | 2026-09-14T04:54:22.501Z `log.message`: "application started" | 确认应用已成功启动的日志记录，缺乏后续的终止或错误日志。 |

**证据说明：**
Kubernetes 状态显示容器已完全就绪（Ready: True），但集群层面判定处于 Terminating 状态。K8s 事件与日志证实了正常启动过程，且重启计数为 0 排除了应用 CrashLoop 的可能。由于 K8s 判定 Terminating 而实际运行状态（Phase: Running）与正常启动证据并存，指向停止流程异常，但缺乏 Kubelet 层面的 kill 日志或应用侧 SIGTERM 捕获日志佐证具体阻塞点。

## 🎯 根因分析 · g1

### 因果链

```text
收到删除请求 (deletionTimestamp已设置) → Kubelet 尝试 Normal Killing → 进程退出受阻 (具体原因未确认) → Pod 保持 Terminating 状态
```

### 根因结论

**证据不足。**

目前的事实（状态 Terminating + 容器 Phase Running + 重启次数 0）高度指向 **Pod Terminating Stuck（终止卡滞）**。这通常由 `preStop` 钩子阻塞、容器内进程未响应 `SIGTERM` 信号或网络/存储卷释放问题引起。

然而，现有证据无法确定具体的阻塞机制：
1. 缺乏 Kubelet 日志证明 `SIGTERM` 或 `SIGKILL` 的发送与结果。
2. 缺乏 `preStop` 钩子的配置及执行日志，无法确认是否为钩子超时或死循环导致。
3. 缺乏应用侧日志证明其如何处理终止信号（如是否卡在文件 I/O 或数据库连接）。

因此，虽能确认“终止受阻”这一现象，但无法给出单一的决定性根因。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 15.3s
├─ 并发证据采集: 119.4s
│  └─ g1 aiops-case-v12/workload: 119.4s (Evidence 108.6s, RCA 10.8s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
