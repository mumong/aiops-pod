## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod workload-5b5fc86c8c-2xgjz 处于 Pending/ContainerCreating 状态，容器未启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `FailedMount`: MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found (fact-bdf37966c24d) | 直接指出挂载失败的具体原因是 ConfigMap 资源缺失 |
| 2 | K8s State | kubelet | `volume: "input"`, `container.waiting_reason: "ContainerCreating"` (fact-555d9dadb03e) | 证实容器因卷挂载问题卡在启动阶段，处于等待状态 |
| 3 | K8s Config | kubelet | Pod Spec 中 `container: "app"` 的资源配置：Request CPU `5m` / Memory `8Mi` (fact-4a8d11d818e9, fact-70d573719df1) | 提供 Pod 调度与资源上下文，排除资源配额导致调度的嫌疑 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 1，`reason: "ContainerCreating"` (fact-ae286078c1a8) | 监控侧数据印证 K8s 状态，确认异常持续且未被自动恢复 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total` 值为 0 (fact-4c693795b0f2) | 确认容器尚未成功启动过，排除了运行后崩溃重启的可能性 |

**证据说明：**
Kubernetes 事件（#1）明确指出了失败机制是 ConfigMap 查找失败，这是导致 Pod 滞留于 `Pending/ContainerCreating` 状态（#2, #4）的根本物理原因。Metric 数据（#4, #5）从独立监控通道佐证了该状态，并确认了无重启计数，说明 Pod 始终未能完成生命周期中的容器启动步骤。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 定义引用不存在的 ConfigMap 'unavailable-config' → Kubelet 挂载卷逻辑报错 (FailedMount) → 容器启动流程被阻塞 → Pod 处于 Pending/ContainerCreating 状态
```

### 根因结论

**已确认的根因：Pod 定义配置错误。**

Pod Spec 中定义的卷 `input` 引用了不存在的 ConfigMap `unavailable-config`。这一配置错误导致 Kubelet 在执行挂载操作时无法找到目标资源，触发 `FailedMount` 事件（证据 #1）。由于挂载是容器启动的前置必要条件，挂载持续失败导致容器进程从未被拉起，从而造成 Pod 长期停留在 `Pending` 或 `ContainerCreating` 状态（证据 #2, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 54.1s
├─ 并发证据采集: 50.8s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 50.8s (Evidence 43.6s, RCA 7.1s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-volume-mount-failed, pod-imagepull-failed
