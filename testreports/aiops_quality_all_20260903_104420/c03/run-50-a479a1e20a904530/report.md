## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod workload-5b5fc86c8c-zz82w 处于 Pending/ContainerCreating 状态，应用容器未启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (重复 x50, x42, 持续 99m+) | 明确故障机制：因缺失 ConfigMap 导致 Kubelet 挂载卷失败 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: `ContainerCreating` | 确认当前容器处于等待挂载依赖项的中间状态 |
| 3 | K8s State | kubernetes | `pod.condition`: `Ready=False (ContainersNotReady)`, `phase: Pending` | 确认 Pod 当前未就绪且未完全调度进入运行状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}`: 值为 1 | 观测到等待状态确证，与 K8s 状态实时一致 |
| 5 | K8s Config | kubernetes | `container.resource_limit.memory`: 32Mi, `container.resource_limit.cpu`: 50m | 排除资源超限导致的 OOMKilled 或 CPU Throttling，辅助验证故障非资源竞争引起 |
| 6 | Tool | kubectl | `configmap unavailable-config not found` | 直接证实故障根本原因：Pod 定义中引用的 ConfigMap 确实不存在 |

**证据关联说明：**
Kubernetes Events (证据 #1) 直接指出了 `unavailable-config` ConfigMap 缺失是挂载失败的核心原因。K8s 状态 (证据 #2, #3) 和 Prometheus 指标 (证据 #4) 分别从控制平面和监控平面交叉验证了该 Pod 长期处于因挂载失败而导致的 `ContainerCreating` / `Pending` 状态。工具实测 (证据 #6) 最终确证了该 ConfigMap 对象不存在，逻辑链条完整闭合。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 不存在于 aiops-case-03 命名空间 → Kubelet 执行 MountVolume.SetUp 失败 (因找不到 ConfigMap 内容) → Pod 挂载卷失败，无法启动应用容器，状态卡在 ContainerCreating → Pod 持续处于 Pending/Unready 状态，应用无法对外提供服务
```

### 根因结论

已确认的根因为：Pod `workload-5b5fc86c8c-zz82w` 的 YAML 定义中声明了一个名为 `input` 的 Volume，该 Volume 引用了 ConfigMap `unavailable-config`。该 ConfigMap 在当前命名空间中实际不存在，导致 Kubelet 在初始化 Pod 时挂载卷失败，从而使得容器无法进入运行状态。

支持证据：
- **事件与状态证据**：K8s Events 报告 `MountVolume.SetUp failed ... configmap "unavailable-config" not found`，且 Pod 处于 `ContainersNotReady` 状态（证据 #1, #2, #3）。
- **观测数据证据**：Prometheus 指标确认了 `waiting_reason` 为 `ContainerCreating` 持续存在（证据 #4）。
- **工具确认证据**：`kubectl get configmap unavailable-config` 返回了 `NotFound` 错误，彻底证实了依赖缺失（证据 #6）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 24.2s
├─ 并发证据采集: 58.7s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 58.7s (Evidence 50.7s, RCA 7.9s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed, pod-oomkilled
