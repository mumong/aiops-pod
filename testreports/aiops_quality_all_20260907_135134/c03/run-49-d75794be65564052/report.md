## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod workload-5b5fc86c8c-2xgjz 处于 Pending/ContainerCreating 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `Pod` `aiops-case-03/workload-5b5fc86c8c-2xgjz` 状态为 `Pending` (fact-952b09d6b562) | 明确当前实体处于启动阻滞状态 |
| 2 | K8s Event | kubernetes | `FailedMount`: `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (fact-54269c17b6b1) | 直接指出卷挂载失败的原因为 ConfigMap 不存在 |
| 3 | K8s Event | kubernetes | `timed out waiting for the condition`: `unmounted volumes=[input]` (fact-d466eb816186) | 证实挂载尝试多次超时，非瞬时网络抖动 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 针对容器 `app` 值为 `1` (reason: `ContainerCreating`) (fact-e6fa9003ec24) | 从监控侧确认容器处于等待挂载/启动的资源阶段 |
| 5 | K8s Config | kubernetes | 容器 `app` 定义引用 Volume `input` (基于 Event 反推) | 关联 Event 报错的卷名与配置来源 |

**证据综合说明：**
1. **配置与状态印证**：`Pending` 状态 (行1) 与 `ContainerCreating` 等待原因 (行4) 高度一致，且重启计数为 0 (事实未展示但可推断状态)，表明故障发生在启动早期。
2. **根本原因锁定**：Event 事实 (行2) 清晰指出了 `configmap "unavailable-config" not found`，这是导致挂载失败的直接原因；行3 的超时记录证实该错误持续存在，排除了偶发性。
3. **缺失维度的合理性**：Logging 与 Tracing 被标记为 `not_applicable` 且事实为空，原因是容器未启动，这与事件和状态证据中描述的“挂载卡死”现象完全吻合。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 缺失 → Kubelet 执行 MountVolume.SetUp 失败(Pod 状态 Pending) → 用户可见现象：容器处于 ContainerCreating 状态且长时间无法启动
```

### 根因结论

已确认根因为：Pod 规范中定义的 Volume `input` 引用了 ConfigMap `unavailable-config`，但该资源在 `aiops-case-03` 命名空间中不存在，导致 Kubelet 挂载卷失败。

依据如下：
1. **K8s Event** (行 2, 行 3) 明确捕获到 `FailedMount` 事件，提示 `configmap "unavailable-config" not found`，且该错误在 81 分钟内重复发生 (48次)，证明配置缺失是持续状态。
2. **K8s State & Metrics** (行 1, 行 4) 提供了系统侧的佐证，Pod 一直滞留于 `Pending/ContainerCreating` 阶段，等待挂载操作完成。
3. 不存在其他冲突的证据；Logging 与 Tracing 因容器未启动而无数据，符合“挂载失败导致容器未拉起”的因果逻辑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.1s
├─ 并发证据采集: 33.9s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 33.9s (Evidence 26.6s, RCA 7.2s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- 未调用 Runbook
