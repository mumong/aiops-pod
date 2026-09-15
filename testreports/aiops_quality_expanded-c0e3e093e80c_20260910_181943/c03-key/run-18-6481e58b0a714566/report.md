## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 处于 ContainerCreating/Pending 状态，挂载 volume 'input' 持续失败超过 22 分钟 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` (`fact-f6020913cb33`) | 直接指出挂载失败的原因为 ConfigMap key 缺失 |
| 2 | K8s Event | kubernetes | `Warning FailedMount ... unmounted volumes=[input]... timed out waiting for the condition` (`fact-719315eb555b`) | 确认挂载卷挂载超时，持续 22 分钟 |
| 3 | K8s State | kubernetes | `Container status: [app] waiting reason: ContainerCreating` (`fact-f4c63e193093`) | 确认容器当前处于挂载/启动阻塞状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` (`fact-6b249f7a0209`) | 从指标维度印证容器处于等待挂载或启动状态 |

上述 K8s 事件明确给出了失败机制（引用不存在的 key），且被 K8s 状态、指标和超时事件相互印证。Logging 与 Tracing 因 Pod 未启动而不可用，不影响该结论的确定性。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 缺少 key 'unavailable-key' → kubelet 挂载 volume 'input' 时 key 校验失败 → MountVolume.SetUp 失败 → Pod aiops-case-v05/workload 卡在 ContainerCreating 状态
```

### 根因结论

已确认的根因是 Pod 的卷配置错误。Pod Spec 中定义的 volume `input` 引用了 ConfigMap `workload-input` 中的 key `unavailable-key`，但该 key 在 ConfigMap 中并不存在（证据 `fact-f6020913cb33`）。这导致 kubelet 在 `MountVolume.SetUp` 阶段无法挂载该卷，并持续失败超过 22 分钟（证据 `fact-719315eb555b`），最终导致容器一直处于 `ContainerCreating` 状态（证据 `fact-f4c63e193093`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 18.6s
├─ 并发证据采集: 35.9s
│  └─ g1 aiops-case-v05/workload: 35.9s (Evidence 28.4s, RCA 7.4s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-volume-mount-failed, pod-sandbox-create-failed, pod-imagepull-failed, pod-config-error
