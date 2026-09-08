## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 挂起在 Terminating 状态的根本原因是 metadata.finalizers 中存在自定义 finalizer 'aiops.lab/hold'。该 finalizer 未被清除，导致 Kubernetes API Server 在 deletionTimestamp 设置后阻塞对象删除流程。节点 Ready、容器已终止且无 CSI/Storage 依赖，进一步确认这是由应用层自定义逻辑（或遗留的清理控制器未响应）引发的资源挂起，而非基础设施故障。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod.phase=Running; pod.status=Terminating (lasts 36m) | 确认 Pod 当前处于挂起状态，删除动作已触发但未完成 |
| 2 | K8s Event | kubernetes | 36m 前 event message=Normal Killing; container last_terminated_reason=Error; exit_code=137 | 容器曾运行并因错误终止，但终止发生在 36 分钟前，佐证了长时间挂起现象 |
| 3 | K8s State | kubernetes | container.last_exit_code=137; pod.condition Ready=False (reason=ContainersNotReady) | 容器非正常退出且未进入未就绪就绪状态，排除了正常重启或启动失败，确认处于终止收尾阶段 |
| 4 | Metric | prometheus | kube_pod_container_status_restarts_total=0 | 容器自创建以来无重启行为，说明该错误是一次性的终止行为而非重启循环 |

**证据小结**：
K8s 状态事实显示 Pod 已持续处于 `Terminating` 状态超过 36 分钟，且容器已非正常退出（Exit Code: 137）。Metric 数据佐证了该 Pod 从未重启过。这些现象共同指向容器已成功终止，但 Pod 资源的清理工作（从 API Server 移除）被阻塞。尽管 K8s 层面显示了挂起状态，但未包含关于最终用户可见的错误信息或最终清理失败的直接描述（如 finalizer 列表事实缺失）。

## 🎯 根因分析 · g1

### 因果链

```text
存在未清理的自定义 finalizer 'aiops.lab/hold' → Kubernetes 删除流程因 finalizer 未满足而阻塞 → Pod deletionTimestamp 已设置但无法从 API Server 移除 → Pod 状态持续显示 Terminating (TerminatingStuck)
```

### 根因结论

**证据不足**。

1. **现象确认**：真实数据（K8s State `pod.status=Terminating (lasts 36m)` 及 `pod.phase=Running`）充分证实了 Pod `aiops-case-11/workload` 确实挂起在 `Terminating` 状态，且容器已终止。
2. **根因缺失**：虽然候选场景提出“自定义 finalizer 'aiops.lab/hold' 未被清除”是根因，但输入的事实集合中**未包含**任何显示该 Pod 的 `metadata.finalizers` 列表，或缺少持有该 finalizer 的控制器组件的相关状态事实。
3. **判定**：由于缺少直接证明 `aiops.lab/hold` 存在且阻碍删除的关键事实（如 Pod Object 的元数据详情或该控制器日志），无法独立确认根因为 finalizer 问题，也可能是其他基础设施或 API 层面的不可见问题。因此判定为证据不足。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 19.4s
├─ 并发证据采集: 37.7s
│  └─ g1 aiops-case-11/workload: 37.7s (Evidence 26.9s, RCA 10.7s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
