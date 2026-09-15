## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 持续处于 ContainerCreating 状态 (Pending)，无法进入 Running。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `ContainerCreating` (Container `app`, fact-2caeeb39af7c) | 确认容器当前处于创建阻塞状态 |
| 2 | K8s State | kubernetes | Pod `Pending`, `ContainersReady=False` (fact-1aee76d43c95, fact-21b2bdddcb33) | 确认 Pod 调度成功但容器未就绪 |
| 3 | K8s Event | kubernetes | `FailedMount`: configmap references non-existent config key: unavailable-key (x35 over 57m, fact-033249526696) | 直接指出挂载失败的具体配置错误 |
| 4 | K8s Config | kubernetes | Volume `input` 引用 ConfigMap (fact-bf45c6569b27) | 提供触发 `FailedMount` 的关联存储卷上下文 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` (fact-8fb5b528692c) | 外部观测确认容器处于等待状态 |

**证据关联说明：**
Kubernetes 事件 `FailedMount` (事实 #3) 明确指出了导致阻塞的原因，即 Pod 配置中引用的 ConfigMap 缺少特定 key。这一配置错误直接阻碍了 Volume `input` (事实 #4) 的挂载，进而导致容器无法完成初始化，表现为 `ContainerCreating` 状态 (事实 #1) 和 `Pending` 阶段 (事实 #2)。Prometheus 指标 (事实 #5) 从外部验证了这一持续存在的等待状态。由于容器未能成功启动，Logging 与 Tracing 维度未产生有效数据。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 缺少 key 'unavailable-key' → MountVolume.SetUp 校验失败 → FailedMount 事件 (Volume 挂载阻塞) → Pod 停留在 ContainerCreating (Pending) 状态
```

### 根因结论

已确认根因：Pod 配置中引用了不存在的配置项。

根据事实 #3，Kubelet 在挂载 Volume 时检测到 ConfigMap 引用的 key `'unavailable-key'` 不存在，直接触发了 `FailedMount` 事件。该错误导致 Pod 的初始化步骤被阻塞，从而使得容器无法进入 `Running` 状态，表现为持续处于 `ContainerCreating` (事实 #1) 和 `Pending` (事实 #2)。现有 Kubernetes 状态、事件及配置事实已充分支撑该因果链，无需补充决定事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 54.8s
├─ 并发证据采集: 41.2s
│  └─ g1 aiops-case-v05/workload: 41.2s (Evidence 33.6s, RCA 7.5s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-volume-mount-failed
