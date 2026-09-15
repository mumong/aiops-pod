## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod workload 处于 Pending/ContainerCreating 状态，容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (kubelet) | `pod.phase: Pending` (fact-19d5965c9d63, fact-5b19ad091034) | 确认 Pod 最终异常状态为 Pending，未进入 Running。 |
| 2 | K8s Event | kubernetes (kubelet) | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` (fact-db488c38ded6) | 直接定位卷挂载失败的具体原因：ConfigMap Key 不存在。 |
| 3 | K8s Event | kubernetes (kubelet) | `Warning FailedMount ... unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition` (fact-b59102af2b9d) | 佐证因卷挂载卡死导致容器初始化失败，进而引发超时。 |
| 4 | K8s State | kubernetes (api) | `container.waiting_reason: ContainerCreating` (fact-bb6845957c10) | 解释用户可见现象：Pod 卡在容器创建阶段，无法启动。 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}: 1` (fact-0eca7e416954) | 独立指标确认当前状态，与 K8s Event 结论一致。 |

**证据互证分析：**
Kubernetes Event（事实 2、3）提供了最直接的失败原因，明确指出 `workload-input` ConfigMap 中引用的 key `unavailable-key` 不存在。这一配置错误导致 `MountVolume.SetUp` 永久失败，进而使 Pod 始终处于 `Pending` 状态且等待原因为 `ContainerCreating`。Prometheus 指标（事实 5）从监控层面印证了 Pod 处于 `ContainerCreating` 等待状态的事实，与 K8s 内部事件完全一致。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap volume 配置引用了不存在的 key: unavailable-key (事实 2) → kubelet 挂载卷失败 (FailedMount) (事实 2, 3) → Pod 无法完成卷初始化，持续处于 Pending 状态 (事实 1, 4) → 用户可见 Pod 处于 ContainerCreating 状态，容器未启动
```

### 根因结论

已确认的根因为 **ConfigMap 挂载配置错误**。具体表现为：Pod 卷定义中引用的 ConfigMap `workload-input` 中，配置了不存在的 key `unavailable-key`。这导致 kubelet 在挂载卷时触发 `FailedMount` 事件并持续超时，使得容器无法进入运行状态。

---

## 📊 性能统计

```text
├─ 总耗时: 51.5s
├─ 问题定位: 13.4s
├─ 并发证据采集: 28.6s
│  └─ g1 aiops-case-v05/workload: 28.6s (Evidence 21.8s, RCA 6.7s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-volume-mount-failed, pod-sandbox-create-failed, pod-imagepull-failed
