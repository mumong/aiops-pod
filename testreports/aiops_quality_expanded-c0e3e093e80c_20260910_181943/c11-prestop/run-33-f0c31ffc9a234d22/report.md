## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod workload (aiops-case-v12) 处于 Terminating 状态滞留 (TerminatingStuck)，phase 显示 Running 但 deletionTimestamp 已设置。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-v12/workload` 处于 `Terminating` 状态，`phase` 为 `Running`，`deletionTimestamp` 已设置（2026-09-14T06:54:27Z） | 确认异常现象：Pod 响应了删除信号但无法完成状态转换 |
| 2 | K8s Config | Kubernetes | `app` 容器的 `preStop` lifecycle hook 逻辑：最长 3600 秒阻塞等待 `/state/teardown-requested` 文件存在 | 确立直接的技术阻碍点：Pod 必须满足文件条件或超时才能停止 |
| 3 | K8s State | Kubernetes | `app` 容器重启次数 (`container.restart_count`) 为 0 | 排除容器因 CrashLoopBackOff 或资源不足被频繁杀死的干扰 |
| 4 | Metric | Prometheus | `kube_pod_status_phase{phase="Running"}` 值为 1，`kube_pod_container_status_restarts_total` 为 0 (2026-09-14T05:50:27.123Z) | 从监控侧面印证 Pod 目前依然处于活动/可运行状态，未因 OOM 等硬限制终止 |
| 5 | Logging | Elasticsearch | 应用日志记录 `application started` (2026-09-14T05:49:34.203Z) | 确认应用本身启动成功，非启动阶段故障 |
| 6 | Topology | Kubernetes | 节点关联与拓扑信息存在，确认 K8s 基础通信链路无大面积阻断 | 排除底层节点失联导致的 Kubelet 通信阻塞 |

**证据关系说明：**
Kubernetes 状态证实了 `Terminating` 滞留，Metric 与 K8s State 确认该滞留不是因为 Crash 而是持续存活。结合 K8s Config 中的 `preStop` hook 配置，形成完整逻辑链：Pod 收到删除信号 -> 触发 hook -> 阻塞等待 3600s -> 滞留。日志确认了应用正常启动，排除了启动即挂的可能。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了最长等待 3600 秒的 preStop hook (等待特定文件) → 触发删除后启动阻塞逻辑 → 因文件未被写入且未超期/GracePeriod耗尽前文件仍未出现 → Pod 保持 Terminating 状态滞留
```

### 根因结论

**已确认根因：** `aiops-case-v12/workload` 的 Pod 规范中配置了 `preStop` lifecycle hook，其逻辑为最长阻塞等待 3600 秒直到 `/state/teardown-requested` 文件存在。当该 Pod 被触发删除（`deletionTimestamp` 已设置）时，容器必须执行该 hook。由于等待文件在预期时间内未出现，且当前尚未达到硬性的 3900s Grace Period 超时（或文件始终缺失导致逻辑阻塞），容器无法发送 SIGTERM/SIGKILL，从而使得 Pod 长期处于 `Terminating` 状态 [证据 1, 2]。

**已知未知：**
1. 谁触发了删除操作（是人工 `kubectl delete` 还是上游控制器）；
2. `/state/teardown-requested` 文件为何未被写入（上游服务是否故障或调用丢失）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 17.6s
├─ 并发证据采集: 60.3s
│  └─ g1 aiops-case-v12/workload: 60.3s (Evidence 47.4s, RCA 12.8s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
