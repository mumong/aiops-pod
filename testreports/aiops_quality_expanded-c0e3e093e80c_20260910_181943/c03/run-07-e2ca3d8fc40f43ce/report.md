## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-xn974 stuck in ContainerCreating/Pending status |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-03/workload-5b5fc86c8c-xn974` 状态为 `Pending` (fact-1f6c42132bde) | 确认 Pod 未处于运行状态，符合待处理异常特征 |
| 2 | K8s Event | kubernetes | 18分钟内 16次 `FailedMount`：`MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (fact-162ddce0fe1d) | 提供挂载失败的直接错误原因，确认依赖资源缺失 |
| 3 | K8s Event | kubernetes | 16分钟内 8次 `FailedMount`：`timed out waiting for the condition` (fact-25ab4172b81b) | 佐证挂载条件长期无法满足，导致 Pod 挂起 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` value `1` (reason=`ContainerCreating`) (fact-f9576012fcf3) | 确认容器处于 `ContainerCreating` 等待状态 |

**证据综合说明：**
K8s 事件明确指出了 Pod 因找不到名为 `unavailable-config` 的 ConfigMap 而导致挂载失败（fact-1 和 fact-2），Metric 数据证实了容器卡在 `ContainerCreating` 阶段的持续状态（fact-3），两者互相印证，排除了其他临时性故障可能。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 在命名空间 aiops-case-03 中缺失 → kubelet 执行 MountVolume.SetUp 失败 → Pod 处于 Pending/ContainerCreating 挂起状态 → 容器无法创建并启动
```

### 根因结论

已确认的根因为 **Volume 挂载配置指向不存在的 ConfigMap**。Pod `workload-5b5fc86c8c-xn974` 的 Volume `input` 引用了 ConfigMap `unavailable-config`，由于该资源在集群中不存在，kubelet 持续挂载失败，导致 Pod 停留在 `Pending` 状态且无法进入 `Running`。此结论由 K8s Event 日志（fact-1, fact-2）与 K8s State 状态（fact-1）及 Metric 监控数据（fact-3）共同确证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 55.5s
├─ 并发证据采集: 26.5s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 26.5s (Evidence 19.7s, RCA 6.7s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-imagepull-failed, pod-volume-mount-failed, pod-config-error
