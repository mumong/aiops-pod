## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Volume 'input' references a ConfigMap key ('unavailable-key') that does not exist in ConfigMap 'workload-input', causing MountVolume.SetUp to fail and preventing the container from starting. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | fact-f32b4de5fd61 | MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key | 明确指出挂载失败机制：ConfigMap 键不存在 |
| 2 | K8s Event | fact-2f0465cd2ceb | FailedMount (x15 over 14m) - Unable to attach or mount volumes: unmounted volumes=[input] | 证实挂载失败为持续异常行为，时间跨度超过 14 分钟 |
| 3 | K8s State | fact-66e07968029e | pod.status = Pending | 定义 Pod 当前因挂载失败导致的终止状态 |
| 4 | K8s Config | fact-2f99fc258bfb | container.restart_count = 0 | 排除因容器运行崩溃导致重启的可能，佐证启动过程卡在挂载阶段 |
| 5 | Metric | fact-54a20d2ce8b7 | waiting_reason = "ContainerCreating" | 量化确认容器等待原因，与 K8s 事件状态一致 |

**证据印证说明：**
Kubernetes 事件（1, 2）直接揭示了“ConfigMap key 不存在”这一具体错误原因，导致 `MountVolume.SetUp` 失败。这种挂载失败直接导致了 Pod 状态停滞在 Pending（3），且由于挂载失败，容器无法启动进入运行状态，因此重启计数保持为 0（4），且 Metric 显示原因持续为 ContainerCreating（5）。各维度证据逻辑闭环，无冲突。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 缺少键 'unavailable-key' → MountVolume.SetUp 失败 → Pod 状态 Pending → 容器无法启动 (ContainerCreating)
```

### 根因结论

已确认根因为：**Pod `aiops-case-v05/workload` 的卷挂载配置错误**。具体而言，其 Volume `input` 引用了 ConfigMap `workload-input` 中的键 `unavailable-key`，但该键在 ConfigMap 中实际并不存在，导致挂载过程失败，进而使 Pod 永远处于 Pending 状态，容器无法启动。该结论由 K8s Event 事实 `fact-f32b4de5fd61` 及 Pod 状态事实 `fact-66e07968029e` 强支持。

---

## 📊 性能统计

```text
├─ 总耗时: 58.4s
├─ 问题定位: 17.0s
├─ 并发证据采集: 33.0s
│  └─ g1 aiops-case-v05/workload: 33.0s (Evidence 27.9s, RCA 5.0s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed
