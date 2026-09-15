## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | {'type': 'ContainersReady', 'status': 'True'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s State | Pod `aiops-case-v12/workload` 状态 `Terminating`；条件 `ContainersReady=True, Ready=True, PodScheduled=True, Initialized=True` (2026-09-14T06:07:12Z) | 表明 Pod 容器已就绪并处于终止生命周期中 |
| 2 | K8s Event | K8s Event | `Normal Killing` (54s前): `kubelet` 执行 `Stopping container app` | 确认 kubelet 已进入容器停止流程 |
| 3 | K8s Config | K8s Config | 容器资源限制: CPU 50m / 内存 32Mi；资源请求: CPU 5m / 内存 8Mi | 提供容器资源边界上下文，无超限配置 |
| 4 | K8s Event | K8s Event | 网络配置记录：Pod IP `172.16.104.29/32`，Calico CNI 已关联 | 网络链路通畅，排除 CNI 初始化失败导致的问题 |
| 5 | K8s State | K8s State | Pod `phase=Running`，重启次数 `0` | 证实容器确实处于运行状态，未发生频繁重启或崩溃 |
| 6 | Logging | Logging | ES日志 (2026-09-14T06:07:18Z): `application started` | 证实容器启动日志已输出，应用生命周期正常 |
| 7 | Metric | Metric | Prometheus 快照 (06:08:02Z): `kube_pod_container_status_waiting_reason=1` (reason: `ContainerCreating`)；`kube_pod_status_phase` 对于 `app` 无 Running 记录，`kube-state-metrics` 处于 Pending | 指标数据呈现 `ContainerCreating` 等待状态，与 K8s State/Logging 事实产生矛盾 |
| 8 | Tracing | Tracing | Deepflow + Tempo 采集结果：无数据 | 无法追踪请求链路以确定应用实际就绪时间 |

**证据关联性说明：**
证据 1、2 与 6 共同证实 Pod 实际已启动并正在被 kubelet 终止。证据 3 与 5 排除了因 OOMKilled 或资源争抢导致频繁重启的可能。证据 7 与前述证据存在直接冲突（指标显示未启动，日志与状态显示已启动），这是当前无法判定确切状态的根本矛盾点。

## 🎯 根因分析 · g1

### 因果链

```text
deletionTimestamp 被设置为未来时间点 (2026-09-14T07:12:12Z) → kubelet 执行 preStop 等待终止信号 → Pod 处于预期的终止等待期内 → Prometheus 指标反映 ContainerCreating 状态与日志显示已启动存在矛盾，状态判定模糊
```

### 根因结论

**证据不足。**

虽然已知 Pod 处于终止等待期（由 `deletionTimestamp` 与 `kubelet` 事件支撑），但目前无法确定导致 `ContainerCreating` 指标与 `Running/Started` 事实矛盾的根源。现有事实无法解释是 Prometheus 抓取延迟、指标状态机滞后，还是 Pod 实际处于“假死”状态。由于缺少描述 `deletionTimestamp` 未来时间设置来源的关键 Topology/Events 证据，以及缺乏 Tracing 数据界定应用的实际启动与就绪时间，无法做出确定性判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 19.5s
├─ 并发证据采集: 57.3s
│  └─ g1 aiops-case-v12/workload: 57.3s (Evidence 46.7s, RCA 10.5s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
