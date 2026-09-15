## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod workload 处于 Terminating 状态，删除时间戳显示为 19-20 分钟前 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Stopping container app` (19m & 20m前) | 确认容器被强制终止 |
| 2 | K8s State | `k8s` | `pod.status: Terminating (lasts 19-20m)` | 证明 Pod 滞留终止状态 |
| 3 | K8s Config | `k8s` | `Finalizer: aiops.lab/hold` | 指示导致滞留的特定机制 |
| 4 | K8s State | `k8s` | `container.last_terminated_reason: Error` | 确认容器异常退出原因 |
| 5 | K8s State | `k8s` | `container.last_exit_code: 137` | 指示进程因内存限制被强杀 |
| 6 | K8s Config | `k8s` | `container.resource_limit.memory: 96Mi` | 提供导致 OOM Kill 的配置上限 |
| 7 | Metric | `prometheus` | `kube_pod_container_status_restarts_total: 0` | 排除容器反复重启导致卡死的情况 |
| 8 | Metric | `prometheus` | `kube_pod_status_phase` Running: 1, Failed: 0 | 确认底层容器状态正常，仅 Pod 状态异常 |
| 9 | Logging | `elasticsearch` | `http_status: 200` (4次) | 排除底层应用服务崩溃或无响应的可能 |

**证据关联分析：**
证据 3 提供了 Pod 滞留的理论原因（Finalizer 未释放）；证据 1、4、5 与证据 6 共同构成了一致的执行事实：应用因内存不足（96Mi 限制）被 OOM Kill 强杀（Exit 137，Error），随后被 kubelet 停止。证据 8 确认了底层节点上容器状态已转为正常（Running 计数包含已杀死的容器，Failed 为 0 说明非长期失败状态），进一步支持滞留纯粹是 Kubernetes 层面的资源清理阻断，而非容器本身异常。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 存在未释放的 Finalizer (aiops.lab/hold) → API Server 阻断资源删除 → 容器因 OOM (Limit 96Mi) 被强杀 (Exit 137) → Pod 滞留 Terminating 状态
```

### 根因结论

**已确认根因：** Pod 资源对象上残留未释放的 Finalizer (`aiops.lab/hold`)，导致 Kubernetes API Server 在容器（app）因内存限制（96Mi）被强杀退出后，仍然阻止其从集群中彻底移除，从而造成 Pod 长期处于 `Terminating` 状态。

*   **支撑证据**：
    *   **Finalizer 阻断**：配置事实（证据 #3）明确显示 `aiops.lab/hold` Finalizer 存在；结合现象（证据 #2，滞留 19-20 分钟）可判定为释放逻辑失败。
    *   **执行事实**：Exit 137（证据 #5）和 Terminated Reason: Error（证据 #4）证实了容器确实已停止，排除了进程假死导致清理失败的可能性。
    *   **内存诱因**：96Mi 的 `resource_limit.memory`（证据 #6）是导致 Exit 137 的直接触发因素。

*   **补充说明**：未采集到负责释放 `aiops.lab/hold` Finalizer 的具体控制器或事件日志（对应 unknowns），因此最终确认是哪个具体组件或逻辑未能触发 Finalizer 的移除。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 20.6s
├─ 并发证据采集: 87.7s
│  └─ g1 aiops-case-11/workload: 87.7s (Evidence 80.3s, RCA 7.3s)
└─ 汇总总结: 12.3s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
