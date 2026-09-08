## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-2xgjz 处于 Pending 状态，容器 app 卡在 ContainerCreating，因 VolumeMount 失败无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount` (fact-1c0c6ca40d15): `timed waiting for the condition` (unmounted volumes=[input]) | 确认直接阻塞机制：kubelet 因卷挂载超时而无法启动容器 |
| 2 | K8s Event | kubernetes | `FailedMount` (fact-b3c7a435c8c5): `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 确立根本原因：名为 'input' 的卷强制依赖缺失的 ConfigMap |
| 3 | K8s State | kubernetes | `ContainerCreating` (fact-7c713c53c663) | 验证容器始终卡在初始化挂载阶段，无法进入运行状态 |
| 4 | K8s State | kubernetes | `phase: Pending` (fact-14350609dfa0, fact-b10655d44b52) | 证实 Pod 处于挂起状态，不可调度运行 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1, reason: `ContainerCreating` (fact-d70e8837a3a8) | 独立观测到容器等待原因为挂载/初始化失败，印证 K8s 状态 |
| 6 | K8s Config | kubernetes | `cpu_request: 5m` (fact-01413e79c5a1), `memory_request: 8Mi` (fact-50611c687977) | 排除资源配额导致 Pending 的可能性，资源请求极低 |

证据印证：K8s 事件 (Fact 1, 2) 明确指出了挂载失败的原因（ConfigMap 'unavailable-config' 缺失）。Metric 数据 (Fact 5) 确认了等待原因为 ContainerCreating，与事件状态一致。配置数据 (Fact 6) 排除了资源限制因素。日志和追踪未采集，但物理上容器未启动，无应用层数据可采集，不影响根因判断。

## 🎯 根因分析 · g1

### 因果链
```text
ConfigMap 'unavailable-config' 在 namespace 'aiops-case-03' 中缺失 → 
Pod Spec 中 volume 'input' 强制依赖该 ConfigMap (Optional=false) → 
Kubelet 执行 VolumeMount.SetUp 时找不到配置资源，触发 FailedMount 事件 → 
容器无法挂载必要卷，状态维持在 ContainerCreating/Pending
```

### 根因结论
已确认根因：Pod `aiops-case-03/workload-5b5fc86c8c-2xgjz` 的 Spec 中定义了一个名为 `input` 的卷，该卷强制依赖 ConfigMap `unavailable-config`。由于该 ConfigMap 在命名空间 `aiops-case-03` 中不存在，kubelet 在挂载卷时失败并永久阻塞，导致 Pod 处于 Pending 状态且容器无法启动。

证据支撑：
- K8s 事件直接报错 `configmap "unavailable-config" not found` (Fact 2, 1)
- K8s 状态和 Metric 一致反映容器卡在 ContainerCreating (Fact 3, 5)
- 资源请求极低 (Fact 6)，排除资源不足导致的 Pending

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 23.6s
├─ 并发证据采集: 40.3s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 40.3s (Evidence 32.3s, RCA 7.8s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-imagepull-failed, pod-sandbox-create-failed, pod-volume-mount-failed
