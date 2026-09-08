## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod 模板中引用的 ConfigMap 'unavailable-config' 不存在，且未在卷定义中设置为 optional，导致 Kubelet 挂载卷失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (fact-d801cb07eba5) | 证实挂载卷失败的根本原因为 ConfigMap 不存在 |
| 2 | K8s Event | kubelet | `FailedMount  2m2s...timed out waiting for the condition` (fact-33aac641fb1c) | 证实由于配置缺失导致的卷挂载超时异常 |
| 3 | K8s State | kubelet | `container.waiting_reason: ContainerCreating` (fact-f93c2ba60582) | 证实应用容器因前置条件（卷挂载）未满足而停留在等待状态 |
| 4 | K8s State | kubelet | `pod.status: Pending`, `ContainersNotReady` (fact-bd4a53531caa, fact-c42c8855a6d0) | 证实 Pod 整体处于调度成功但容器未就绪的失败等待期 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (reason=ContainerCreating) (fact-237bbdf423f5) | 从指标侧独立印证了容器等待挂载的真实状态 |

证据说明：Kubernetes 事件明确指出了具体的缺失资源（ConfigMap），而 Metric 数据验证了这一等待状态的持续存在，两者共同构成了完整的证据链。日志和链路追踪因容器未启动而无数据，但这符合预期。

## 🎯 根因分析 · g1

```text
ConfigMap 'unavailable-config' 缺失 → 卷挂载超时/失败 → 容器处于 ContainerCreating 等待状态 → Pod 持续 Pending 且未 Ready
```

### 根因结论

已确认的根因是 Pod 模板引用的 ConfigMap `unavailable-config` 不存在。Kubelet 在尝试挂载卷时发现配置缺失且未在卷定义中标记为可选，从而引发挂载超时（Fact 1, 2），导致容器无法启动并停留在 `ContainerCreating` 状态（Fact 3, 4, 5）。

---

## 📊 性能统计

```text
├─ 总耗时: 54.9s
├─ 问题定位: 18.7s
├─ 并发证据采集: 28.7s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 28.7s (Evidence 24.0s, RCA 4.6s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-imagepull-failed, pod-sandbox-create-failed, pod-volume-mount-failed
