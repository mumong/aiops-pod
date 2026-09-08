## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod workload-5b5fc86c8c-zz82w 卡在 ContainerCreating (Pending) 阶段，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase: Pending`, `pod.status: Pending` (fact-4c4cd03ade3b, fact-ab321417761b) | 确认 Pod 处于调度后、运行前状态，与现象一致。 |
| 2 | K8s Event | kubernetes | `FailedMount`: "MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found" (fact-385b63ff6cab, fact-88b701484c31) | 直接定位卷挂载失败原因：ConfigMap 不存在。 |
| 3 | K8s Event | kubernetes | `FailedMount`: "timed out waiting for the condition" (fact-6dfee1997107, fact-eab156e17836) | 说明故障持续发生且重试失败，导致 Pod 无法推进。 |
| 4 | K8s State | kubernetes | `container.waiting_reason: ContainerCreating` (fact-19059bf47411) | 确认应用容器未启动，符合挂载阻塞表现。 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` (fact-1fa7760156dd) | 指标状态独立证实容器处于等待状态，与 K8s 事件相互印证。 |
| 6 | Metric | prometheus | `kube_pod_container_resource_requests{memory="8388608"}` (fact-13d64c39bb68) | 资源请求量为 8Mi，排除了因资源不足导致 Pending 的可能性。 |

**证据分析**：Kubernetes 事件 (Fact 2, 3) 明确指出是因为 ConfigMap "unavailable-config" 缺失导致 `input` 卷挂载失败。由于该挂载失败，Pod 无法启动容器，表现为 `ContainerCreating` 状态 (Fact 4)。Metric 数据 (Fact 5, 6) 排除了资源不足等其他 Pending 原因，并佐证了容器始终处于等待状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用不存在 ConfigMap 'unavailable-config' (optional=false) → Kubelet 挂载卷 'input' 失败 → 持续触发 FailedMount 事件 → Pod 卡在 ContainerCreating 状态
```

### 根因结论

已确认根因为 **Pod 依赖的 ConfigMap "unavailable-config" 不存在**，导致挂载失败。
- **根因事实**：K8s 事件显示 `configmap "unavailable-config" not found` (证据 2, 3)。
- **影响路径**：挂载失败导致容器无法启动，Pod 状态保持为 Pending/ContainerCreating (证据 1, 4, 5)。
- **剩余未知**：ConfigMap "unavailable-config" 是意外被删除还是从未创建，目前无日志证据支持判断。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 35.7s
├─ 并发证据采集: 63.9s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 63.9s (Evidence 53.5s, RCA 9.9s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-imagepull-failed, pod-volume-mount-failed
