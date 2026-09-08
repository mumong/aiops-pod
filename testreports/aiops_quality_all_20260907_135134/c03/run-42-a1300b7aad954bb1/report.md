## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod 定义中引用了不存在的 ConfigMap 'unavailable-config' 作为卷 'input'，导致 kubelet 挂载卷持续失败，Pod 卡在 ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-bf96b814dba6` | `Warning FailedMount` ... MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found | 直接指出根因：ConfigMap 缺失导致挂载失败 |
| 2 | K8s State | `fact-24b2559e994b` | `container.waiting_reason`: reason="ContainerCreating" | 描述 Pod 因等待资源挂载而卡在启动阶段的状态 |
| 3 | K8s State | `fact-45ae929b7899` | `pod.phase`: Pending | 宏观状态确认 Pod 无法进入运行阶段 |
| 4 | Metric | `fact-233e939ea5ee` | `kube_pod_container_status_waiting_reason` (reason="ContainerCreating"): 1 | 验证了 K8s 观测到的 ContainerCreating 等待状态 |
| 5 | Metric | `fact-dc5c3d5de12a` | `kube_pod_container_status_restarts_total`: 0 | 确认应用尚未启动，排除应用崩溃重启场景 |

**证据总结**
Kubernetes Event（#1）明确记录了 `unavailable-config` ConfigMap 缺失导致卷挂载失败（`FailedMount`），这直接解释了 Pod 为何因资源无法就绪而处于 `ContainerCreating` 状态（#2, #3, #4），且由于容器从未启动，因此未发生任何重启（#5）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义引用不存在的 ConfigMap (unavailable-config) → Kubelet 挂载卷 (input) 失败 → 容器启动阻塞 → Pod 卡在 ContainerCreating 状态
```

### 根因结论

已确认根因：Pod 的 YAML 定义中引用了一个不存在的 ConfigMap `unavailable-config` 作为卷 `input`。由于该配置项缺失，kubelet 在执行 `MountVolume.SetUp` 时失败，导致容器无法完成初始化挂载，从而使 Pod 持续处于 `ContainerCreating` 和 `Pending` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 40.0s
├─ 并发证据采集: 36.6s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 36.6s (Evidence 32.0s, RCA 4.4s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-volume-mount-failed
