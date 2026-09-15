## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | {'type': 'Ready', 'status': 'True'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | `pod.status`: `Terminating (lasts <invalid>)`, `pod.phase`: `Running` | 确认 Pod 处于 Terminating 卡滞状态，与容器仍在运行的状态存在逻辑冲突 |
| 2 | K8s State | `kubernetes` | `pod.condition`: `Ready=True`, `ContainersReady=True` (2026-09-14T05:46:29Z) | 证明容器进程在删除指令下发后仍保持活跃并响应就绪检查 |
| 3 | K8s Event | `kubernetes` | `Normal Killing`: `Stopping container app` (62s) | 标记了终止流程的起点，但缺乏 Killing 动作完成后的后续事件 |
| 4 | K8s Config | `kubernetes` | `resource_request`: `memory=8Mi`, `cpu=5m`; `resource_limit`: `memory=32Mi`, `cpu=50m` | 排除资源超卖导致的 OOM 或 CPU 节流 |
| 5 | Metric | `prometheus` | `kube_pod_container_status_restarts_total`: `0` | 证实应用为单生命周期实例，不存在反复重启导致的删除竞争 |
| 6 | Logging | `elasticsearch` | `log.message`: `application started` (2026-09-14T05:46:37.205Z) | 确认应用启动成功，但未采集到应用日志中关于 graceful shutdown 的信息 |
| 7 | Tracing | `deepflow+tempo` | `coverage: empty` | 缺乏应用层的执行链路数据，无法分析 shutdown hook 执行情况 |

**证据综合说明：**
1. **状态矛盾**：K8s 报告 (Fact 1, 2) 显示 Pod 仍在 `Running` 且 `Ready`，这与 `Terminating` 状态相互矛盾，直接证实了删除过程的停滞。
2. **缺失执行层事实**：仅有 K8s 层面发出的 Killing 事件 (Fact 3) 和容器存活证据 (Fact 4, 5)，缺乏容器运行时实际停止进程的记录。
3. **日志断档**：应用日志 (Fact 6) 仅记录了启动，未提供退出信号处理期间的信息；Tracing (Fact 7) 数据缺失，导致无法追溯应用内部或中间件在接收到终止请求时的具体行为。

## 🎯 根因分析 · g1

### 因果链

```text
API Server 标记删除(deletionTimestamp) → [未确认] Kubelet 停止容器进程失败/卡住 → 容器持续响应 Ready → Pod 卡在 Terminating (lasts <invalid>)
```

### 根因结论

**诊断结论：证据不足 (inconclusive)**

现有证据仅能确认 `aiops-case-v12/workload` 出现了标准的 `Terminating` 卡滞现象，但无法定位具体的执行故障点：

1. **已确认事实**：Pod 对象在 API Server 中标记为删除，kubelet 触发了 `Killing` 事件，但容器进程未退出（Phase 仍为 Running，Restarts 为 0），导致删除流程无法完成。
2. **缺失的关键决定性事实**：
   - **容器运行时层**：缺少 `containerd/crictl` 实际执行停止操作的日志或耗时记录。无法确定是 kill 信号被忽略、SIGKILL 失败，还是运行时本身卡住。
   - **清理侧翼**：无法判断 kubelet 是在等待容器退出，还是在执行 `volume detach` / `network cleanup` 时发生了阻塞。
   - **状态异常**：Pod 的 `lasts` 字段显示 `<invalid>`，暗示状态机更新出现异常，但未提供导致状态机卡死的具体底层错误。

鉴于缺少执行层（Runtime/Plugin）的失败原因记录，无法区分是应用层未处理信号、Kubelet 逻辑阻塞还是存储/网络插件的清理卡死。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 27.3s
├─ 并发证据采集: 105.5s
│  └─ g1 aiops-case-v12/workload: 105.5s (Evidence 95.6s, RCA 9.8s)
└─ 汇总总结: 13.2s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
