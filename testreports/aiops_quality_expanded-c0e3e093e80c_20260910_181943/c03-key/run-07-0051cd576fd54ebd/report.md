## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 处于 ContainerCreating/Pending 状态，容器无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning FailedMount  62s (x12 over 9m16s) MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` | 确诊根因，指明 ConfigMap 挂载失败的具体键名 |
| 2 | K8s State | kubelet | `Pod aiops-case-v05/workload` 处于 `Pending` 状态，`container.app` 重启计数 `0` | 确认容器未进入运行阶段，无启动失败重排记录 |
| 3 | K8s Event | kubelet | `Warning FailedMount  20s (x4 over 7m13s) Unable to attach or mount volumes: unmounted volumes=[input]` | 佐证挂载动作因配置依赖缺失而受阻 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 `1`，`reason="ContainerCreating"` | 确认 Pod 处于创建等待阶段，与 K8s Event 状态一致 |
| 5 | K8s Config | kubelet | `container.app` 内存请求 `8Mi`，限制 `32Mi`；CPU 请求 `5m`，限制 `50m` | 排除资源不足引发的调度或运行瓶颈 |

**证据印证关系**：
K8s Event (fact-7d5f45a798f0) 和 Metric (fact-7c173a67f567) 明确显示 Pod 卡在 `ContainerCreating` 阶段。Event (fact-e5c9ce0e4ac5) 直接给出了失败的因果解释：ConfigMap 键 `unavailable-key` 不存在，导致 `FailedMount`。K8s State 确认重启计数为 0，证实问题处于初始化挂载阶段而非容器启动后。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap workload-input 缺少 key unavailable-key → kubelet 挂载 volume 'input' 时校验配置键失败 → VolumeMount failed 导致容器无法完成初始化 → Pod 状态停留在 Pending/ContainerCreating
```

### 根因结论

已确认的根因是 Pod spec 中引用的 ConfigMap `workload-input` 中不存在键 `unavailable-key`，导致 kubelet 挂载卷失败 (FailedMount)，容器持续等待。

证据支撑：
- **直接证据**：K8s Event (fact-e5c9ce0e4ac5) 明确报告 `configmap references non-existent config key: unavailable-key`，直接指向配置缺失这一根本原因。
- **状态佐证**：K8s State (fact-2556fe7c4bb7) 和 Metric (fact-7c173a67f567) 证实 Pod 停留在 `ContainerCreating/Pending` 状态，且未发生重启（fact-3065b638917e, restart_count=0），这与挂载失败导致的初始化卡死现象完全吻合。

未确认项：
- ConfigMap `workload-input` 的实际可用 keys 列表。
- `unavailable-key` 是拼写错误还是上游配置变更导致丢失。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 46.4s
├─ 并发证据采集: 40.1s
│  └─ g1 aiops-case-v05/workload: 40.1s (Evidence 32.2s, RCA 7.7s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-volume-mount-failed
