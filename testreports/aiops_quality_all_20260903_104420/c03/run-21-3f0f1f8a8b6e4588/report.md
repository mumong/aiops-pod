## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-zz82w stuck in ContainerCreating/Pending |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `failedmount` (fact-78c441803482) | `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 直接揭示挂载失败的根本原因：引用的 ConfigMap 不存在 |
| 2 | K8s Event | `failedmount` (fact-50830607ceb6) | `Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition` | 证实挂载阻塞导致容器无法进入运行状态 |
| 3 | K8s State | `pod.condition` (fact-da7166371292) | `Ready=False` (`reason=ContainersNotReady`, `message=containers with unready status: [app]`) | 反映容器因挂载依赖未满足而卡在非就绪状态 |
| 4 | K8s State | `waiting_reason` (fact-2588325d1e5c) | `ContainerCreating` | 明确当前容器生命周期处于等待依赖准备阶段 |
| 5 | Metric | `kube_pod_container_status_waiting_reason` (fact-e0234cc817db) | `1` (labels: `container=app`, `reason=ContainerCreating`) | 独立确认应用容器当前等待原因 |
| 6 | K8s Config | `container.resource_request.cpu` (fact-714434ede6c9) | `5m` | 排除低 CPU 请求导致调度或启动延迟的可能性 |
| 7 | K8s Config | `container.resource_request.memory` (fact-6b6a17fca2b3) | `8Mi` | 排除低内存请求导致调度或启动延迟的可能性 |

证据链表明：指标（#5）与容器状态（#3）均显示容器处于 Waiting/Created 阶段，K8s 事件（#1, #2）给出了具体的等待原因：挂载卷 `input` 失败，因为所需的 ConfigMap `unavailable-config` 不存在。资源配置（#6, #7）显示请求量极低，排除了资源不足导致的调度或启动延迟。日志与追踪工具因容器未启动而无数据。

## 🎯 根因分析 · g1

### 因果链

```text
缺少 ConfigMap 'unavailable-config' → 卷 'input' 挂载配置失败 → 容器 'app' 卡在 ContainerCreating → Pod 持续处于 Pending 且应用不可访问
```

### 根因结论

**已确认根因：Pod 规范中声明挂载的 ConfigMap 'unavailable-config' 在命名空间 'aiops-case-03' 中不存在。**

事实证据支撑（#1, #2）明确显示 `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found`。这一错误直接导致 `ContainerCreating` 状态（#3, #4, #5），并阻止了容器的就绪状态（#3）。由于挂载操作在容器启动阶段阻塞，容器物理上无法运行，因此日志与追踪数据（#6, #7）在此场景下不适用且无法收集。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 21.0s
├─ 并发证据采集: 47.4s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 47.4s (Evidence 42.0s, RCA 5.2s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed, pod-sandbox-create-failed, pod-imagepull-failed, pod-config-error
