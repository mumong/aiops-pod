## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod 'workload' 的 volume 'input' 配置引用了 ConfigMap 'workload-input' 中不存在的 key 'unavailable-key'，且该 Volume 未标记为 optional，导致 Kubelet 挂载卷失败，Pod 持续处于 ContainerCreating/Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` (fact-8f5ef6e3048a) | 提供直接错误机制，指出挂载失败的具体原因是引用了不存在的 ConfigMap Key |
| 2 | K8s Event | kubernetes | `Warning FailedMount ... timed out waiting for the condition` (fact-48cba54dbd7b) | 佐证挂载阻塞导致的超时现象 |
| 3 | K8s State | kubernetes | `pod.phase: Pending` (fact-0a3c350bb59a) | 确认 Pod 处于预期异常状态，无法进入运行阶段 |
| 4 | K8s State | kubernetes | `container.waiting_reason: ContainerCreating` (fact-100750033d50) | 确认容器因挂载阶段受阻而等待 |
| 5 | K8s Config | kubernetes | `resource_limit.memory: 32Mi` (fact-36043f170e97) | 确认容器资源限制并非导致挂载失败的直接原因 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1` (fact-b8e0020fd701) | 独立验证 K8s 状态中记录的等待原因 |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total{container="app"} = 0` (fact-73cb556fd5c9) | 排除应用启动后崩溃重启的可能性，确认为启动前阻塞 |

**证据说明：**
K8s Event 中的 `FailedMount` 直接给出了失败原因（Fact 1），与 Pod 状态的 `Pending` 和 `ContainerCreating` 一致（Fact 3, 4）。Metric 数据独立印证了容器的等待状态（Fact 6）和零重启记录（Fact 7），排除了其他运行时故障。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 缺少 key 'unavailable-key' → Pod 配置请求挂载该 key 且 optional=false → Kubelet FailedMount: configmap references non-existent config key → Pod 卡在 ContainerCreating/Pending 状态
```

### 根因结论

**已确认的根因：** Pod 的 `volume` 配置（名为 `input`）引用了 ConfigMap `workload-input` 中不存在的 Key `unavailable-key`。

**分析：**
Kubelet 在挂载卷时检测到配置中的 Key 不存在，且该卷未标记为 `optional: true`，导致挂载操作失败（直接体现为 Event `FailedMount`）。这阻止了容器启动，使 Pod 持续处于 `ContainerCreating` 状态。

**未知项：** 现有证据无法区分是 ConfigMap `workload-input` 本身完全不存在，还是该 ConfigMap 存在但确实缺少 `unavailable-key` 这个键值对。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 25.6s
├─ 并发证据采集: 31.9s
│  └─ g1 aiops-case-v05/workload: 31.9s (Evidence 24.4s, RCA 7.4s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed
