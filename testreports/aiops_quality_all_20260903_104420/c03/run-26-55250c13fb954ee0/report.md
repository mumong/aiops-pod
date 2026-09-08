## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-zz82w 处于 ContainerCreating/Pending 状态，未就绪。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `fact-7244eefe9b78`: `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (重复 28 次) | 直接证明缺失 ConfigMap 导致卷挂载失败 |
| 2 | K8s Event | `kubernetes` | `fact-e7a5108a6b85`: `Warning FailedMount ... unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition` (重复 20 次) | 确证挂载超时机制 |
| 3 | K8s State | `kubernetes` | `fact-6b188dce4307`: `pod.status` = `Pending` | 确认 Pod 因挂载问题阻塞在调度/挂载阶段 |
| 4 | K8s State | `kubernetes` | `fact-a597a85b0934`: `app` 容器状态 `ContainerCreating` | 排除容器启动失败，定位到挂载环节 |
| 5 | K8s Config | `kubernetes` | `fact-2b54fced5035`: CPU limit `50m`; `fact-14627627fb54`: Memory request `8Mi` | 排除资源配额不足导致的调度失败 |
| 6 | Metric | `prometheus` | `fact-a1a2e3cd4c30`: `kube_pod_container_status_waiting_reason` `reason="ContainerCreating"` 值为 `1` | 辅助印证容器处于挂载/等待阶段 |

**证据关联说明：**
K8s Event (事实 1, 2) 明确指出了“configmap unavailable-config not found”这一错误原文，与 K8s State (事实 3) 中 Pod 处于 `Pending` 状态及 `ContainerCreating` 状态相互印证，共同指向卷挂载这一特定失败环节，排除了 CPU/内存资源不足或容器应用崩溃的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 缺失 → kubelet 挂载卷失败 → VolumeMount 错误 → Pod 处于 Pending/ContainerCreating 状态
```

### 根因结论

**已确认根因**：Pod `aiops-case-03/workload-5b5fc86c8c-zz82w` 的 `input` 卷定义指向了 ConfigMap `unavailable-config`，但该 ConfigMap 在 `aiops-case-03` 命名空间中不存在。
**证据支撑**：K8s Event 中重复出现的 `configmap "unavailable-config" not found` 错误原文 (事实 1) 以及 `unmounted volumes=[input]` 状态 (事实 2)，确证了挂载环节因配置缺失而阻塞，导致容器无法进入运行状态。
**未确认事实**：ConfigMap 缺失的根本业务原因（如是否遗漏部署、命名拼写错误或版本不匹配）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 30.9s
├─ 并发证据采集: 47.1s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 47.1s (Evidence 39.8s, RCA 7.2s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed
