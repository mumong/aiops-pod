## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod `workload` 的 YAML 配置引用了 ConfigMap `workload-input` 中不存在的键 `unavailable-key`，导致卷挂载失败，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount` 11s (x7 over 43s) `MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` | **直接证据**：确认卷挂载失败，明确报错原因为 ConfigMap 键缺失。 |
| 2 | K8s State | kubernetes | `container.waiting_reason` = `ContainerCreating` (fact_id: `fact-0c68fa46ab64`) | **现象支撑**：容器卡在创建阶段，未进入运行状态。 |
| 3 | K8s State | kubernetes | `pod.status` = `Pending` (fact_id: `fact-f7b763fa66a4`) | **现象支撑**：Pod 整体调度停留在 Pending 状态，无法进入 Scheduling 完成阶段。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = `1` (reason=`ContainerCreating`) (fact_id: `fact-700979cb1492`) | **多维印证**：Metric 状态与 K8s Event 描述一致，确认等待原因。 |
| 5 | K8s Config | kubernetes | `container.resource_limit.memory` = `32Mi` / `cpu` = `50m` | **上下文**：资源限制极小，排除资源超限导致调度失败的干扰。 |
| 6 | K8s State | kubernetes | `restart_count` = `0` (fact_id: `fact-42e8a336498d`) | **排除干扰**：排除因 OOM 或 CrashLoopBackOff 导致的重启问题。 |

**证据说明**：K8s Event (`#1`) 提供了明确的失败原因（引用了不存在的 ConfigMap 键 `unavailable-key`），该事件直接导致了 K8s State (`#2`) 中的 `ContainerCreating` 和 `Pending` 状态。Metric (`#4`) 独立观测到的 `waiting_reason` 与 Event 原因一致，证实了该挂载失败是当前主要阻塞点。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 配置引用 ConfigMap 键 `unavailable-key` → 卷挂载组件校验失败 (FailedMount) → 容器启动受阻 → Pod 保持 ContainerCreating/Pending 状态
```

### 根因结论

**已确认的根因**：Pod `workload` 的 YAML 配置引用了 ConfigMap `workload-input` 中不存在的键 `unavailable-key`，导致 Kubernetes 无法完成卷挂载，进而使容器无法启动。

- **证据支撑**：Event `FailedMount` (`fact-da6bca47ce1f`) 明确指出了具体的失败路径和缺失键名；等待原因 Metric (`fact-700979cb1492`) 和状态事实 (`fact-0c68fa46ab64`) 佐证了该挂载错误是当前唯一的阻塞现象。

---

## 📊 性能统计

```text
├─ 总耗时: 58.5s
├─ 问题定位: 14.3s
├─ 并发证据采集: 33.9s
│  └─ g1 aiops-case-v05/workload: 33.9s (Evidence 28.1s, RCA 5.7s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-volume-mount-failed
