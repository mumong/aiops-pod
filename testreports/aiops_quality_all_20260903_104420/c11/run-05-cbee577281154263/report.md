## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod workload in aiops-case-11 stuck in Terminating phase |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | pod phase: Running; status: Terminating (lasts 9m14s); Ready/ContainersReady: False (reason: ContainersNotReady) | 确认 Pod 处于终止停滞状态，已 9 分 14 秒未彻底销毁，且容器不可用 |
| 2 | K8s State | Kubernetes | container.app exit_code: 137; reason: Error; restart_count: 0 | 容器 app 因退出码 137（OOM Kill）终止，且未发生重启 |
| 3 | K8s Event | Kubernetes | Normal Killing 9m13s kubelet Stopping container app; Exit Code: 137 | 确认 kubelet 已执行停止容器的动作，证实异常发生时刻 |
| 4 | Metric | Prometheus | kube_pod_container_status_restarts_total=0; kube_pod_status_phase=1 (Running) | 证实容器终止后未重启，且 Pod 仍处于活跃状态而非 Succeeded |
| 5 | Logging | Elasticsearch | pattern: http_request completed (path: /work, status: 200); numeric_field: allocated_mib (min: 0, max: 0) | 提供终止前最后时刻的业务日志，证明应用此前正常运行，且未显示内存增长过程（可能受限于观测点） |
| 6 | Tracing | Tempo | trace_id: 75c4028b11532f074defb107fd297f49; span: GET /work, status: 200, duration: 3us | 关联日志时间窗，确认应用在被杀前成功响应了 HTTP 请求 |

**证据关联说明：**
证据 1、2、3 形成了“容器 OOM 终止（退 137）→ 节点执行停止动作 → 但 Pod 整体状态卡在 Terminating”的直接状态矛盾。证据 4 从指标层面佐证了 Pod 未进入 Succeeded 或 Failed 的最终状态。证据 5、6 作为上下文，确认了终止发生在正常业务请求期间，排除了应用主动退出的可能。关于“自定义 Finalizer 阻塞”的根因结论，当前 K8s 事实中未包含 metadata.finalizers 列表的具体值（如 `aiops.lab/hold`），该关键证据缺失。

## 🎯 根因分析 · g1

### 因果链

```text
Container app killed due to OOM (exitCode=137, fact-2) → [未确认: Finalizer 'aiops.lab/hold' 阻止垃圾回收] → Pod object stuck in Terminating phase, lasting 9m14s (fact-1) → 集群资源泄漏 (无法调度新 Pod)
```

### 根因结论

现有证据**不足**以确认最终根因。

虽然事实清楚表明容器 `app` 因 **OOM (Exit Code 137)** 被强制终止，且 Pod 正处于 **Terminating** 状态长达 9 分钟，但 K8s 层面缺少决定性的事实来解释为何终止过程被阻塞。

1.  **已验证部分**：触发事件确认为容器 OOM Kill (fact-2, fact-3)。
2.  **缺失的决定性事实**：要解释为何 Pod 卡在 Terminating 状态，必须确认 Pod 的 `metadata.finalizers` 字段中是否存在未清理的自定义 Finalizer（如输入中提示的 `aiops.lab/hold`），且缺乏该 Finalizer 被移除的证据。当前所有 K8s 状态事实均未展示 `finalizers` 列表。

因此，无法断言“Finalizer 阻塞”是事实，只能确认是候选场景。需补充查询该 Pod 的 YAML `metadata` 信息以完成诊断。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 21.1s
├─ 并发证据采集: 36.3s
│  └─ g1 aiops-case-11/workload: 36.3s (Evidence 29.7s, RCA 6.4s)
└─ 汇总总结: 12.8s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
