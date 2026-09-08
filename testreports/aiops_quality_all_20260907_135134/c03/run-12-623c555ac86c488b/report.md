## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-2xgjz stuck in ContainerCreating/Pending state, volume mount failure |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount` 34s (x19 over 23m) `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 直接原因：Volume挂载因ConfigMap缺失被Kubelet拒绝 |
| 2 | K8s Event | kubernetes | `Warning FailedMount` 30s (x10 over 21m) `Unable to attach or mount volumes: unmounted volumes=[input]` | 状态持续：挂载阻塞导致Pod持续无法进入运行状态 |
| 3 | K8s State | kubernetes | `container.waiting_reason`: `ContainerCreating` | 现象确认：容器卡在创建阶段，未启动且未重启 |
| 4 | K8s State | kubernetes | `pod.phase`: `Pending`; `pod.condition[Ready]`: `False` (reason: `ContainersNotReady`) | 状态确认：Pod整体处于Pending阶段，不符合预期就绪 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason[reason="ContainerCreating"]` = `1` (timestamp: 08:31:35Z) | 观测佐证：Prometheus侧指标持续确认Pod处于Wait状态 |
| 6 | K8s Config | kubernetes | 资源配置: CPU Request `5m`, Limit `50m`; Memory Request `8Mi`, Limit `32Mi` | 排除干扰：资源请求量极小，排除因资源不足导致调度失败 |

**证据关联说明：**
K8s Events (fact-6c, fact-c1) 提供了决定性的失败机制解释，明确指出 volume `input` 因引用不存在的 `unavailable-config` ConfigMap 而挂载失败。K8s State (fact-66, fact-43) 和 Metric (fact-97) 相互印证了故障的持续状态（ContainerCreating），且重启次数为 0 (fact-7d)，排除了容器启动后崩溃导致等待的可能，确认故障发生在容器启动前阶段。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 缺失 (g1) → Kubelet尝试挂载引用该ConfigMap的Volume失败 (机制) → 触发FailedMount事件并阻塞挂载 (直接失败) → Pod 卡在 ContainerCreating/Pending 状态 (现象)
```

### 根因结论

已确认根因为 **Pod 挂载的 Volume 引用的 ConfigMap 不存在**。

具体而言，Pod `aiops-case-03/workload-5b5fc86c8c-2xgjz` 的 Volume `input` 绑定了名为 `unavailable-config` 的 ConfigMap，但该 ConfigMap 在 `aiops-case-03` 命名空间中并不存在。由于 Kubelet 在启动容器前必须完成所有 Volume 的挂载，这一缺失直接导致挂载过程失败并产生持续的错误事件 `configmap "unavailable-config" not found` [证据 #1, #2]，使得 Pod 无法通过 `ContainersNotReady` 检查，长期停滞在 `ContainerCreating` 状态 [证据 #3, #4]。Metric 数据 [证据 #5] 和极低的资源配置 [证据 #6] 均不支持资源不足或其他外部因素，确认为单一的配置依赖缺失导致。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 28.8s
├─ 并发证据采集: 29.4s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 29.4s (Evidence 19.3s, RCA 10.0s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-imagepull-failed, pod-volume-mount-failed, pod-config-error
