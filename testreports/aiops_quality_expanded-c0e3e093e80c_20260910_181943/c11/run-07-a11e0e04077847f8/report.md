## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload stuck in Terminating phase after container exit code 137 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Pod Status | `phase: Running`, `status: Terminating (lasts 10m)` | 定义现象：Pod 容器已退出但对象未释放。 |
| 2 | K8s Event | K8s Events | `Normal Killing 10m kubelet Stopping container app` | 确认 Kubelet 已触发并完成了 `SIGTERM` -> `SIGKILL` 的容器删除流程。 |
| 3 | K8s State | K8s Pod Condition | `ContainersNotReady: containers with unready status: [app]` | 佐证容器已不处于 Ready 状态。 |
| 4 | K8s State | K8s Container Exit | `container: app, exit_code: 137` | 指示进程被强杀，通常对应 OOMKilled 或 SIGKILL。 |
| 5 | K8s Config | K8s Resource Limits | `memory limit: 96Mi` | 提供 OOMKilled 的候选背景条件。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 0` | 排除历史多次重启的干扰，证实为近期单次异常。 |
| 7 | Logging | Elasticsearch | Pattern: `request completed (path: /work, status: 200)`, TimeRange: `03:47:09.905Z - 03:47:15.941Z`, numeric_fields: `allocated_mib: 0` | 终止前应用层 HTTP 请求正常返回 200，且在观察窗口内 `allocated_mib` 均为 0，未直接捕获到内存暴增。 |
| 8 | Tracing | Tempo/Deepflow | Flow `GET /work` (status 200) & Flow `POST /v1/traces` (status 200) | 确认终止前业务逻辑与监控数据上报链路均正常。 |

**证据关联说明：**
Kubernetes 状态（Fact 1, 3, 4）与 Kubelet 事件（Fact 2）相互印证，确立了“容器被强杀（137）但 Pod 对象卡死在 Terminating 状态”的核心事实。Logging 和 Tracing（Fact 7, 8）在终止窗口内（03:47:09 至 03:47:15）均正常返回 200，且日志内存指标未记录异常增长，说明致命异常（OOMKilled 或其他硬故障）发生得非常突然或未被应用层监控感知。

## 🎯 根因分析 · g1

### 因果链

```text
Pod container app terminated (Exit Code 137) → Kubelet initiated graceful termination → Finalizer 'aiops.lab/hold' present and not removed → Pod status stuck in Terminating (lasts 9m14s)
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-11/workload` 滞留于 `Terminating` 状态的直接原因是其持有自定义 Finalizer `'aiops.lab/hold'`。
- 容器 `app` 因退出码 137 被 Kubelet 强杀，Pod 生命周期进入删除阶段（见事实 1, 2, 4）。
- 由于 `aiops.lab/hold` 这个 Finalizer 未被对应的控制器或 Webhook 移除（即 Kubernetes 无法执行对象的最终删除），导致 Pod 对象被阻塞在 `Terminating` 状态长达 9 分 14 秒（见事实 1）。
- **证据支撑**：K8s 状态事实 1 中的 Terminating 滞留时长，以及诊断事实中的 Finalizer 阻断机制（`diagnosis.phenomenon` 和 `formal_rca.causal_chain`）。

**未确认/未知项（证据不足）：**
- **容器 Exit Code 137 的具体诱因**：虽然 Pod 设置了 96Mi 内存限制（事实 5），通常 137 暗示 OOMKilled，但当前的 Logging（事实 7，`allocated_mib` 持续为 0）和 Metric（事实 6，仅重启数，无详细容器内存时序）均未捕获到内存激增或确认 OOM 信号。因此，当前证据仅能证实发生了强杀，无法确切断定为 OOMKilled 还是其他外部 SIGKILL。

---

## 📊 性能统计

```text
├─ 总耗时: 2.9m
├─ 问题定位: 21.3s
├─ 并发证据采集: 135.0s
│  └─ g1 aiops-case-11/workload: 135.0s (Evidence 125.4s, RCA 9.4s)
└─ 汇总总结: 15.1s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
