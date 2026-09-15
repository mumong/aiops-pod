## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | {'type': 'ContainersReady', 'status': 'True'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `deletionTimestamp` 06:58:02Z 设置；Phase: `Running`；Conditions: `Ready`/`ContainersReady`/`Initialized` 均为 `True` | 确认 Pod 处于正常终止窗口内，且内部容器进程未异常退出 |
| 2 | K8s Config | Kubernetes | `terminationGracePeriodSeconds` 3900s (65分钟)；资源限制 `cpu: 50m`, `memory: 32Mi` | 确认终止超时策略，当前现象未超出设定的宽限期 |
| 3 | K8s Event | Kubernetes | `app` 容器 `restart_count: 0` | 排除因资源不足或应用崩溃导致的重启可能 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 0；`kube_pod_status_phase`: Running(1), Unknown(0) | 验证当前运行时长及资源监控指标符合终止等待期的预期 |
| 5 | Logging | Elasticsearch | `2026-09-14T05:53:08.502Z`: "application started" | 确认应用已成功启动，当前状态为长时间运行等待 |
| 6 | Tracing | DeepFlow/Tempo | 聚合记录为空，无匹配 Span | 确认无法通过调用链判定应用内阻塞位置，但无证据显示应用本身报错 |

**证据说明：**
Kubernetes 状态与 Prometheus 指标一致证实容器在 termination 后保持 Running 且未重启。日志表明应用已正常启动。尽管配置了 65 分钟的 Grace Period，但应用侧日志未能覆盖终止阶段的 Hook 执行情况，Tracing 数据缺失进一步限制了我们对“PreStop Hook 阻塞”这一具体机制的确认。

## 🎯 根因分析 · g1

### 因果链

```text
deletionTimestamp 已设置 (06:58:02Z) 触发终止 → 应用 PreStop Hook 阻塞等待特定文件信号 (尚未验证) → Pod 保持 Running 状态消耗 Grace Period 窗口 → 用户可见 Terminating 现象
```

### 根因结论

**证据不足**。

1.  **现象确认**：Pod `aiops-case-v12/workload` 处于 `Terminating` 状态，已设置 `deletionTimestamp`，且 `phase` 仍为 `Running`。
2.  **缺失的决定性事实**：
    *   **未确认阻塞点**：虽然形式 RCA 推测为 `PreStop Hook` 等待 `/state/teardown-requested` 文件，但当前输入缺乏该 Hook 执行的日志或 Trace 证据（Logging 仅显示应用启动，Tracing 为空），无法证实 Hook 是否正在执行以及是否处于阻塞状态。
    *   **未确认时间进度**：缺乏当前精确时间与 `deletionTimestamp` 的差值对比。在 `terminationGracePeriodSeconds=3900s` 的宽限期背景下，若时间未耗尽，当前现象属于**正常等待**而非故障。

结论需要确认应用内部的 Hook 日志或证明等待时间已接近超时边界，以区分“正常终止等待”与“异常卡死”。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 22.9s
├─ 并发证据采集: 34.6s
│  └─ g1 aiops-case-v12/workload: 34.6s (Evidence 25.2s, RCA 9.3s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
