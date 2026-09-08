## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod workload-5b5fc86c8c-zz82w (aiops-case-03) 持续处于 ContainerCreating 状态，无法进入 Running。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.phase`: Pending; `pod.status`: Pending | 确认 Pod 未进入运行状态 |
| 2 | K8s Config | Kubernetes | `container.waiting_reason`: ContainerCreating | 确认容器处于等待启动的阶段 |
| 3 | K8s Event | Kubernetes | `FailedMount`: MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found | 直接定位到挂载失败原因是 ConfigMap 不存在 |
| 4 | K8s State | Kubernetes | `pod.condition`: ContainersReady/Ready 均为 False (ContainersNotReady) | 佐证容器尚未启动 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason`: 1 (reason=ContainerCreating, container=app) | 独立证实 K8s 状态中的等待原因，支持挂载受阻推断 |

**证据交叉印证：**
K8s 事件 (事实 #3) 明确指出 volume "input" 因找不到 configmap "unavailable-config" 而挂载失败，这直接解释了 K8s 状态 (事实 #1, #2, #4) 中 Pod 持续 Pending 且处于 ContainerCreating 阶段的原因。Metric 数据 (事实 #5) 确认了 waiting_reason 与 K8s 事件及状态完全一致。

## 🎯 根因分析 · g1

### 因果链
```text
ConfigMap 'unavailable-config' 不存在于命名空间 aiops-case-03 → Volume 'input' 挂载初始化失败 (MountVolume.SetUp failed) → Pod 无法启动容器，保持 ContainerCreating 状态 → 用户可见 Pod 持续 Pending/ContainerCreating 且伴随 FailedMount 事件
```

### 根因结论
已确认根因：**Pod 定义引用的 ConfigMap 'unavailable-config' 缺失导致挂载失败。**
证据编号 #3 (K8s Event) 提供了决定性证据，显示 kubelet 在执行 Volume "input" 挂载时明确报错 "configmap 'unavailable-config' not found"。该错误阻断了 Pod 的启动流程，导致容器卡在 `ContainerCreating` 阶段无法就绪。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 26.4s
├─ 并发证据采集: 61.7s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 61.6s (Evidence 52.2s, RCA 9.3s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed
