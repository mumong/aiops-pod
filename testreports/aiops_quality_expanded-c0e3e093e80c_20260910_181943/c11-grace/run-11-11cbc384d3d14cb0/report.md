## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload 处于 Terminating 状态（deletionTimestamp 已设置，但 phase 仍为 Running 且容器未退出），显示“卡死”现象。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod | phase=Running, deletionTimestamp已设置, ContainersReady=True, restarted=0 | 证明 Pod 处于删除等待期，但容器本身健康且未发生重启 |
| 2 | K8s Config | Pod Spec | terminationGracePeriodSeconds=3900s (65分钟) | 设定了极长的优雅终止宽限期，解释了为何 1 分钟的等待不会触发强制 KILL |
| 3 | Logging | Elaticsearch | 时间序列: [06:50:53] application started -> [06:50:55] SIGTERM received; waiting | 捕获了应用接收到终止信号并进入自定义等待逻辑的确切行为 |
| 4 | Metric | Prometheus | `kube_pod_status_phase` Running=1, `kube_pod_container_status_restarts_total`=0 | 通过监控数据独立印证了 Pod 仍处于 Running 阶段且无崩溃重启现象 |
| 5 | Metric | Prometheus | `kube_pod_status_phase` Unknown=0 | 排除 Pod 失联或未响应的可能性，确认 API Server 正常记录其运行状态 |

**证据关联说明：**
K8s 状态与 Metric 的 `phase=Running` 相互印证，确认 Pod 未被调度节点抛弃。Logging 中的 "SIGTERM received; waiting" 结合 K8s 配置中的 `terminationGracePeriodSeconds=3900s`，解释了为何在收到删除信号 1 分钟后，Pod 依然处于正常的 Terminating 流程中，未出现异常僵死或快速重启。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 删除操作 (deletionTimestamp 已设置)
  → Kubernetes 发送 SIGTERM 信号，启动 3900 秒宽限期计时
  → 应用容器接收信号，执行自定义逻辑：等待 /state/teardown-requested 文件出现
  → 文件尚未出现，应用保持 "waiting" 状态
  → Pod phase 维持在 Running，表现为 Terminating 状态长期挂起
```

### 根因结论

**已确认根因：** Pod 处于正常的优雅终止流程中，因应用自定义了等待特定文件 (`/state/teardown-requested`) 的 SIGTERM 处理程序，且集群配置的终止宽限期较长（65分钟），导致删除操作在未满足应用退出条件前不会强制终止。

**证据支持：**
*   **机制确认：** 日志证据 (#3) 直接记录了应用收到信号后的等待行为。
*   **现象解释：** K8s 配置 (#2) 提供了长达 3900 秒的宽限期事实，解释了为何 1 分钟的等待（当前时刻距离删除请求仅约 1 分钟）表现为正常的 Terminating 而非异常停滞。
*   **状态佐证：** 状态证据 (#1) 与监控证据 (#4, #5) 确认 Pod 未被驱逐或崩溃，符合等待中的预期表现。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.7s
├─ 并发证据采集: 38.0s
│  └─ g1 aiops-case-v13/workload: 38.0s (Evidence 26.8s, RCA 11.2s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
