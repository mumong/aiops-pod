## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod 'workload' 被施加了自定义 finalizer 'aiops.lab/hold'，在删除请求发出后，由于该 finalizer 对应的控制器或逻辑未执行或未成功移除该标记，导致 Kubernetes API Server 拒绝清理 Pod 资源对象。尽管容器进程因内存不足（OOMKilled, exitCode 137）已终止，且 deletionTimestamp 已设定超过78分钟，但 finalizer 的存在强制 Pod 保持在 Terminating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.status | `Terminating (lasts 78m)` | 确认 Pod 处于卡死状态，删除请求已发出但未完成 |
| 2 | K8s State | container.last_exit_code | `exit_code: 137` | 证明容器进程因内存不足（OOMKilled）异常终止 |
| 3 | K8s State | pod.condition | `ContainersReady: False` (last: 2026-09-03T22:31:15Z) | 确认容器当前处于不可用状态 |
| 4 | K8s State | event.message | `Exit Code: 137` (record_count: 6) | 提供容器被终止的直接系统事件佐证 |
| 5 | K8s Config | container.resource_limit.memory | `96Mi` | 提供导致 OOM 的关键资源约束背景 |
| 6 | Metric | kube_pod_deletion_timestamp | `1788474663` (sample_count: 61) | 确认删除时间戳长期存在，且数值与 K8s 状态中的 78m 时长相符 |

**证据说明**
1. **现象确认**：Pod 实体状态显示 `Terminating` 长达 78 分钟（Fact 1），且容器退出码明确为 `137`（Fact 2），配合 K8s 事件确认了 OOMKilled 的终止原因。
2. **状态持久性**：Prometheus 指标显示 `deletion_timestamp` 在长采样窗口内数值固定（Fact 6），证实了 Pod 并未正常清理，而是卡在 Kubernetes 对象生命周期中的特定阶段。
3. **缺失信息**：Logging 与 Tracing 维度均为空（`status: absent`），无法获取容器进程 OOM 发生前的具体行为或日志记录，因此仅能通过 K8s 状态推断其因资源限制而崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 Finalizer 'aiops.lab/hold' 未释放 → API Server 拒绝清理资源 → 强制维持 Terminating 状态 → 删除请求卡死 >78分钟
```

### 根因结论

**已确认的根因**：Pod `aiops-case-11/workload` 被施加了自定义 Finalizer `aiops.lab/hold`，该标志位阻止了 Kubernetes 对象存储的清理流程。

**分析细节**：
1. 尽管容器因内存不足（`exit_code: 137`, 限制 `96Mi`）已终止，且 `deletionTimestamp` 已超过 78 分钟，但 Pod 仍无法进入 `Terminated` 或被移除状态（证据 1, 2, 5, 6）。
2. 这种“卡死”现象符合 Kubernetes 删除 Finalizer 机制的特征，即当 Pod 存在未处理的 Finalizer 且对应的控制器未将其移除时，API Server 会永久保留该对象处于 `Terminating` 状态。
3. **未知部分**：现有 K8s 状态与指标仅能证明 Finalizer 的存在与状态，无法确认注册该 Finalizer 的具体控制器（谁注册的）及其未能自动释放的具体逻辑条件（证据不足）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 23.2s
├─ 并发证据采集: 61.2s
│  └─ g1 aiops-case-11/workload: 61.2s (Evidence 52.3s, RCA 8.8s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
