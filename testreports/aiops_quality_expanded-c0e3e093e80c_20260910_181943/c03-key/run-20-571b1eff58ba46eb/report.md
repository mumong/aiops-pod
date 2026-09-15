## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod workload (aiops-case-v05) is stuck in ContainerCreating/Pending state with repeated FailedMount events, preventing the container from starting. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount`: MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key (Repeated x19 over 25m) [fact-9fbe77edeea9] | 直接证明挂载失败的根本原因：配置项缺失 |
| 2 | K8s Event | kubernetes | `FailedMount`: Unable to attach or mount volumes: unmounted volumes=[input] (Repeated x10 over 23m) [fact-e962409168a9] | 补充证据：显示挂载操作持续处于超时/重试状态 |
| 3 | K8s State | kubernetes | `pod.status` = "Pending" | 确认 Pod 当前停滞状态 |
| 4 | K8s State | kubernetes | `container.waiting_reason` = "ContainerCreating" [fact-ff1615f9e555] | 确认容器处于等待初始化资源的阶段 |
| 5 | K8s State | kubernetes | `pod.condition`: ContainersReady/Ready = "False" (Reason: ContainersNotReady) [fact-36b2a1fdfc08, fact-38fee891a32b] | 确认 Pod 未就绪 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (container="app", reason="ContainerCreating") = 1 [fact-761d8b988aae] | 指标数据印证 K8s Event 中的等待状态 |

证据之间形成了闭环：K8s Event 1 与 2 明确指出挂载卷 `input` 因 ConfigMap 键 `unavailable-key` 不存在而失败；Pod 状态 3、4 及 Condition 5 与 Metrics 6 一致地反映了 Pod 因此处于 `Pending/ContainerCreating` 状态且未能就绪。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 中不存在 'unavailable-key' (未确认完整内容，但错误明确) → Pod 中 Optional=false 的 Volume 挂载配置引用了该缺失的 Key → Kubelet 执行 MountVolume.SetUp 失败 → Pod 卡在 ContainerCreating/Pending 状态，无法启动容器
```

### 根因结论

**已确认根因**：Pod `aiops-case-v05/workload` 的卷配置错误。

该 Pod 的容器 `app` 在 `ContainerCreating` 阶段被阻塞，直接原因是 Kubelet 在尝试挂载名为 `input` 的卷时失败。错误日志 `configmap references non-existent config key: unavailable-key` 确凿地表明，该卷被配置为挂载 ConfigMap `workload-input` 中的键 `unavailable-key`，但该键在 ConfigMap 中不存在，且由于挂载配置为 `Optional=false`，导致挂载操作不可恢复并引发重试直至 Pod 状态停滞（证据 1、2）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 22.6s
├─ 并发证据采集: 39.4s
│  └─ g1 aiops-case-v05/workload: 39.4s (Evidence 30.4s, RCA 8.8s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-sandbox-create-failed, pod-imagepull-failed, pod-config-error
