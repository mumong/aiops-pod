## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 持续处于 ContainerCreating 状态，未能就绪。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount 17s (x13 over 10m) kubelet MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` | 揭示挂载失败的确切原因，确认配置引用错误事实 |
| 2 | K8s Event | kubernetes | `Warning FailedMount 97s (x4 over 8m30s) kubelet Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition` | 确认挂载失败是持续性的，并非瞬时错误 |
| 3 | K8s State | kubernetes | `Pod status: Pending` | 确认 Pod 停留在初始化阶段，未进入运行态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (`reason: ContainerCreating`, `container: app`) | 确认应用容器正处于等待阶段 |

**证据说明：**
- 事件 `fact-0f3eb93fc80e` 直接指出了根因：ConfigMap 中引用的 key `unavailable-key` 不存在，导致挂载机制（机制 `fact-0f3eb93fc80e`）无法完成，Pod 因此卡在 `Pending` 状态 `fact-8274d24cdeab`。
- K8s 状态与指标相互印证，均显示容器处于 `ContainerCreating` 或 `Pending` 的阻塞阶段，未发生重启 `fact-2f05f667d8c4`。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap volume 引用了不存在的 key 'unavailable-key' → MountVolume.SetUp 持续失败 → 容器挂载阶段阻塞，Pod 卡在 Pending → 应用容器无法启动，持续处于 ContainerCreating 状态
```

### 根因结论

已确认的根因是 Pod 定义中 ConfigMap volume `input` 引用了不存在的 key `unavailable-key`。该配置错误导致 Kubelet 在执行挂载操作时持续失败，直接阻碍了容器的启动流程。
- 事件 `fact-0f3eb93fc80e` 提供了决定性证据，明确指出了缺失的 key。
- 状态 `fact-8274d24cdeab` 和指标 `fact-28e5b3d80260` 证实了挂载失败导致的持续阻塞现象。
- 现有证据充分，无需补充决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 26.7s
├─ 并发证据采集: 46.2s
│  └─ g1 aiops-case-v05/workload: 46.2s (Evidence 38.5s, RCA 7.6s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed
