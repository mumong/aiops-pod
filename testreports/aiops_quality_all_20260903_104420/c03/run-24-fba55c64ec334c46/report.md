## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod workload-5b5fc86c8c-zz82w 处于 Pending / ContainerCreating 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount... MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (fact-68c2d953b0b3, fact-6b690bb5ec0f) | 证实 Pod 启动失败的直接原因：引用了不存在的 ConfigMap，且该卷配置为必选挂载。 |
| 2 | K8s Event | kubernetes | `Warning FailedMount... Unable to attach or mount volumes... timed out waiting for the condition` (fact-76743cb4f027, fact-c55f9ff51573) | 佐证上述错误，显示挂载卷失败后 kubelet 持续重试并超时，导致 Pod 停滞。 |
| 3 | K8s State | kubernetes | `Pod status: Pending`, `container status: ContainerCreating` (fact-3624924f58fe) | 反映异常现象，Pod 卡在初始化阶段，容器尚未启动。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` (fact-579357e792ac) | 独立监控指标确认容器处于等待挂载或初始化状态，与 K8s 事件一致。 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total = 0` (fact-e536a34ca7ff) | 排除因容器运行后崩溃（OOM/Crash）导致重启的可能，指向启动前失败。 |

**证据分析：**
Kubernetes 事件明确指出了资源引用缺失（ConfigMap "unavailable-config"）是挂载失败的直接原因；Metric 数据中的等待原因为 `ContainerCreating` 且重启次数为 0，排除了运行时崩溃，证实故障发生在容器启动前的挂载阶段。两者高度一致，共同锁定根因为配置错误。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 定义了非可选 ConfigMap volume 'input' 引用不存在的资源 → kubelet 挂载卷失败 (FailedMount) → 容器持续等待挂载且超时 → Pod 卡在 Pending / ContainerCreating 状态
```

### 根因结论

已确认根因为：Pod `workload-5b5fc86c8c-zz82w` 的规范中声明了一个名为 `input` 的卷，该卷指向 ConfigMap `unavailable-config`，但该 ConfigMap 在 `aiops-case-03` 命名空间中不存在，且卷定义未开启 `Optional: true`。

这导致 kubelet 在尝试挂载卷时直接报错 `configmap "unavailable-config" not found` [证据#1]，由于挂载失败且无其他备选卷，Pod 无法推进到 Running 状态，持续重试并最终表现为 `timed out waiting for the condition` [证据#2]。Metric 中的 `ContainerCreating` 状态和 0 重启次数 [证据#4, #5] 进一步确认了故障处于启动准备阶段，而非运行后故障。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 20.4s
├─ 并发证据采集: 63.4s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 63.4s (Evidence 54.3s, RCA 8.9s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed, pod-pending-unschedulable, pod-imagepull-failed
