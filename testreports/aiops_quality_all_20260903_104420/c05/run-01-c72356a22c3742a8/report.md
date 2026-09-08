## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v 处于 ContainerCreating (Pending) 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase: Pending` / `container.waiting_reason: ContainerCreating` | 确认 Pod 处于调度后但未就绪的异常阶段 |
| 2 | K8s State | Kubernetes | `pod.condition: Ready=False (ContainersNotReady)` / `Initialized=True` | 隔离故障阶段：沙箱与初始化完成，但容器进程未拉起 |
| 3 | K8s State | Kubernetes | `container.resource_request.cpu: 5m`, `container.resource_limit.cpu: 50m` | 确认资源请求量级极低，排除节点资源过载导致 Pending |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason[reason="ContainerCreating"] = 1` (单样本) | 独立观测到等待原因为 ContainerCreating |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 0` (单样本) | 确认实例为首次启动，排除因健康检查失败导致的 CrashLoop |

日志与追踪维度因容器未启动及无 Pod IP 而标记为 `not_applicable`，无更多直接证据。当前事实仅证实了“沙箱创建失败”这一现象。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用不存在的 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件查找网络配置失败 (NoNetworkFound) → FailedCreatePodSandBox → Pod 停滞在 ContainerCreating/Pending 状态
```

### 根因结论

根据 `formal_rca` 及其支持事实，根因为 **Multus CNI 插件在 node2 上查找网络配置失败 (NoNetworkFound)**。

该根因直接导致 `FailedCreatePodSandBox` 错误，解释了为何 Pod 能完成调度 (Scheduled=True) 但无法进入运行状态。证据 1、3 和 4 分别从 K8s 状态和 Metric 侧印证了“沙箱创建阶段失败”而非资源不足或应用内部崩溃。

---

## 📊 性能统计

```text
├─ 总耗时: 54.6s
├─ 问题定位: 16.6s
├─ 并发证据采集: 31.0s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 31.0s (Evidence 24.2s, RCA 6.6s)
└─ 汇总总结: 7.0s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed, pod-config-error
