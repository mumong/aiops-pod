## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload stuck in ContainerCreating state due to FailedMount |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `fact-a735e31809e8` Warning FailedMount: MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key | 确定挂载失败的根本原因，指向 ConfigMap 中的无效引用 |
| 2 | K8s Event | kubernetes | `fact-fd0360b1a5e4` Warning FailedMount: unmounted volumes=[input]: timed out waiting for the condition | 确认挂载尝试已发生并超时，印证了 Volume 配置问题 |
| 3 | K8s State | kubernetes | `fact-14128f3b1f64` Pod status: Pending | 确认 Pod 最终状态为 Pending |
| 4 | Metric | prometheus | `fact-343d8531d3ab` waiting_reason=ContainerCreating, value=1 | 辅助确认容器当前处于等待挂载资源的状态 |

证据 1 提供了具体的错误原由：`configmap references non-existent config key: unavailable-key`。这一结果被证据 2 的超时报错所验证，说明 kubelet 因无法获取该 Key 而持续尝试挂载并最终失败。证据 3 和 4 分别从 Pod 状态和 Metrics 角度反映了该失败导致的最终现象。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 中引用了不存在的 key 'unavailable-key' → kubelet 执行 MountVolume.SetUp 失败 → 卷挂载超时 → Pod 卡在 Pending/ContainerCreating 状态
```

### 根因结论

已确认根因为 **Volume 挂载配置错误**。
Pod `aiops-case-v05/workload` 尝试挂载名为 `input` 的卷时，因引用的 ConfigMap `workload-input` 中缺失指定的 key `unavailable-key`，导致 `MountVolume.SetUp` 失败并超时，最终使容器无法启动，Pod 保持 Pending 状态（证据 1、2）。

---

## 📊 性能统计

```text
├─ 总耗时: 53.8s
├─ 问题定位: 25.3s
├─ 并发证据采集: 21.3s
│  └─ g1 aiops-case-v05/workload: 21.3s (Evidence 14.8s, RCA 6.5s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed
