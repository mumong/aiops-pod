## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod workload-5b5fc86c8c-xn974 stuck in ContainerCreating/Pending |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedMount` `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (fact-adf7cdc094f1) | 确认根因：缺少 ConfigMap 导致挂载阻断 |
| 2 | K8s Event | Kubernetes | `timed out waiting for the condition` (fact-d8a24d5465bb) | 解释持续阻塞：kubelet 超时重试 |
| 3 | K8s State | Kubernetes | `container.waiting_reason: ContainerCreating` (fact-a3e383bee7bd) | 确认现象：容器未能启动 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` (fact-c3fa039ed63b) | 独立观测：确认状态与 K8s 事实一致 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 0` (fact-00ae44eb0d81) | 排除干扰：确认并非容器崩溃重启导致 |

**证据关系说明**：
K8s Event 提供了直接失败原因（ConfigMap 缺失），Metric 数据独立验证了该 Pod 一直处于 `ContainerCreating` 等待状态且未发生任何重启，两者互相印证故障机制。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 配置引用不存在的 ConfigMap 'unavailable-config' → 卷挂载失败且未设置 optional=true → 挂载操作超时重试 → 容器始终处于 ContainerCreating 状态
```

### 根因结论
**已确认的根因**：Pod `workload-5b5fc86c8c-xn974` 的配置错误导致挂载失败。

故障由 K8s 调度/状态层面的直接事实支撑（证据 #1, #2, #3）。Pod 尝试挂载名为 "input" 的卷，但该卷依赖的 ConfigMap `unavailable-config` 在 namespace `aiops-case-03` 中不存在。由于配置未将其设为可选挂载（optional=false），kubelet 陷入重试并超时（证据 #2），导致容器永久卡在等待状态（证据 #3, #4），且未引发应用层面的崩溃重启（证据 #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 21.3s
├─ 并发证据采集: 44.1s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 44.1s (Evidence 35.5s, RCA 8.5s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-sandbox-create-failed, pod-imagepull-failed
