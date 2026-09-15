## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod spec 中 volume 'input' 引用了 ConfigMap 'workload-input' 中不存在的 key 'unavailable-key'，导致 Kubelet 无法挂载卷，Pod 卡在 ContainerCreating 阶段。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` | 确认 Kubelet 挂载卷失败的根本原因是 ConfigMap 键不存在 |
| 2 | K8s Event | kubernetes | `Warning FailedMount ... Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition` | 确认挂载超时及资源未就绪状态 |
| 3 | K8s State | kubernetes | `container.waiting_reason: "ContainerCreating"` | 确认容器处于启动等待阶段 |
| 4 | K8s State | kubernetes | `pod.status: "Pending"` | 确认 Pod 处于挂起状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 确认容器等待原因指标状态 |
| 6 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"} = 1` | 确认 Pod 生命周期阶段状态 |
| 7 | K8s State | kubernetes | `failed_tool_attempts: kubectl logs ... container "app" in pod "workload" is waiting to start: ContainerCreating` | 确认容器未运行，无法获取日志，与状态一致 |

**证据关联说明**：
Kubernetes Event (1, 2) 提供了具体的失败原因（ConfigMap key 缺失），直接解释了 K8s State (3, 4) 中 Pod 卡在 `Pending/ContainerCreating` 的原因。Metric (5, 6) 从外部观测确认了与 K8s 状态一致的等待阶段。日志工具 (7) 因容器未启动而失败，反向证实了容器未进入运行状态的推断。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 中缺少 key 'unavailable-key' (证据 #1) 
→ 导致 Kubelet 无法完成 volume 'input' 挂载 
→ 触发 FailedMount 警告与挂载超时 (证据 #2) 
→ Pod 卡在 ContainerCreating 阶段，状态为 Pending (证据 #3, #4, #5, #6)
```

### 根因结论

已确认的根因是 **Pod spec 中 volume 'input' 引用了 ConfigMap 'workload-input' 中不存在的 key 'unavailable-key'**。
- 证据 #1 (`MountVolume.SetUp failed`) 明确指出了挂载失败的确切原因。
- 证据 #3 和 #5 确认了容器因此卡在 `ContainerCreating` 状态。
- 证据 #2 确认了挂载操作因条件未满足而超时。
- 所有证据共同指向配置引用错误导致的启动阻塞，无其他竞争因素或异常状态干扰。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 37.4s
├─ 并发证据采集: 37.0s
│  └─ g1 aiops-case-v05/workload: 37.0s (Evidence 31.4s, RCA 5.5s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-volume-mount-failed, pod-config-error
