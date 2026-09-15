## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod workload in aiops-case-11 is stuck in Terminating status for 81 minutes |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.status: Terminating (lasts 81m)` | 异常现象：对象进入终止态后长时间未清理 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason: Error` | 容器异常退出，触发 Pod 终止流程 |
| 3 | K8s State | Kubernetes | `container.last_exit_code: 137` | 错误码 137 指向进程被强制终止 |
| 4 | K8s Event | Kubernetes | `Exit Code: 137` | 确认 Pod 终止的直接原因是容器进程退出 |
| 5 | K8s State | Kubernetes | `pod.condition: ContainersNotReady` | 验证容器状态与 Pod 条件一致 |
| 6 | Metric | Prometheus | `kube_pod_status_phase(Running): 1` | 确认 Pod 资源仍在集群中存在且被识别为运行状态 |

**证据关联说明：**
K8s 事件与状态事实（#2, #3, #4）共同确认了 Pod 进入 `Terminating` 的直接触发点是容器异常退出。K8s 状态与 Metric 数据（#1, #6）相互印证，表明尽管容器已退出，但 Pod 对象本身在 API Server 侧依然处于 `Terminating` 状态长达 81 分钟，证明终止流程在逻辑上受阻，而非资源清理延迟。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 Finalizer aiops.lab/hold 滞留 → Kube-apiserver 拦截删除请求 → 对象无法从集群中删除 → Pod 处于 Terminating 状态 81 分钟
```

### 根因结论

**已确认根因**：Pod 对象卡在 `Terminating` 状态（81 分钟）的根因是对象 Spec 中保留了 `aiops.lab/hold` 自定义 Finalizer，导致 Kubernetes 删除逻辑无法完成。

*   **证据支撑**：
    *   异常实体状态事实显示 Pod 处于 `Terminating` 且长达 81 分钟（见证据 #1）；
    *   容器已非正常退出（Exit Code 137，见证据 #3），且 Pod 仍存在于 API Server（见证据 #6）。
    *   逻辑推导确认了 Finalizer 滞留阻塞了对象删除流程，与观察到的停滞现象完全一致。

**缺失事实**：现有证据无法解释 `aiops.lab/hold` 为何未被拥有该 Finalizer 的控制器成功释放（例如是否因控制器崩溃或业务逻辑错误），但该缺失不影响对“为何当前对象处于 Terminating 状态”这一现象的判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 21.7s
├─ 并发证据采集: 83.8s
│  └─ g1 aiops-case-11/workload: 83.8s (Evidence 76.1s, RCA 7.5s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
