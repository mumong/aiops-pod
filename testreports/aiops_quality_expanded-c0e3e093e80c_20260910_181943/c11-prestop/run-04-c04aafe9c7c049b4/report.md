## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | {'type': 'PodScheduled', 'status': 'True'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | phase: Running; condition: PodScheduled/Initialized/Ready/ContainersReady (True); restart_count: 0 | 证实 Pod 处于正常运行状态且未重启，确认资源配置（Request: 8Mi/5m, Limit: 32Mi/50m）正常。 |
| 2 | Metric | prometheus | `kube_pod_container_status_restarts_total` = 0; `kube_pod_status_phase` Running=1, Failed=0 | 佐证无应用崩溃或异常终止记录，无 Failed 状态出现。 |
| 3 | Logging | elasticsearch | message: "application started" | 确认应用已启动，但缺乏退出或终止相关的后续日志记录。 |
| 4 | K8s Event | kubernetes | 未检测到失败事件 (如 ForceKill, FailedKill) | 排除因资源超限或健康检查失败导致的强制终止现象。 |

**证据关联说明：**
- K8s State (fact-257c4cf30922) 与 Metric (fact-a43f97e667bb, fact-1006c835a875) 相互印证，确认 Pod 未经历异常重启或崩溃。
- 缺乏 Tracing 数据且日志仅显示启动，无法确认应用内部是否正处于等待终止信号或文件存在性检查的逻辑中，但无证据表明进程已死锁。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 被请求终止（基于诊断报告推断） → 应用可能因检查 /state/teardown-requested 文件是否存在而挂起（正常逻辑） → Pod 处于 Terminating/Running 的未决状态 → 现象为 Pod 无法自动消失
```
*注：终止机制中的“应用等待”环节为基于逻辑的推演，当前无直接文件状态或集群当前时间事实支撑，标记为未确认环节。*

### 根因结论

**证据不足。**

虽然 Pod 状态显示为 Running 且存在 Terminating 的潜在请求（参考诊断报告中的 unknowns），但现有证据缺失关键的判定基准：
1. **无法确认是否超期**：缺乏“当前集群时间”与“deletionTimestamp”的对比事实，无法确认是否已超过 65 分钟（3900s）的 `terminationGracePeriodSeconds`。
2. **缺乏异常证据**：未观察到 `ForceKill`、`FailedKill` 等事件，也未检测到应用进程非正常退出（重启计数为 0），无法排除这只是一个正常的等待过程。
3. **状态未决**：缺少容器当前详细状态（如 Waiting Reason）以及应用内部文件 `/state/teardown-requested` 的存在性事实。

在无法确认当前时间与删除请求间隔是否过长的情况下，无法判定为异常故障。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 19.6s
├─ 并发证据采集: 44.4s
│  └─ g1 aiops-case-v12/workload: 44.4s (Evidence 34.8s, RCA 9.6s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
