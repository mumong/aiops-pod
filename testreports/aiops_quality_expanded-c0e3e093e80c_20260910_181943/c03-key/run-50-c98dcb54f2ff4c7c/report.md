## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod 'workload' in namespace 'aiops-case-v05' is stuck in 'ContainerCreating' / 'Pending' status for over 78 minutes. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` (fact-86c016f70b3e) | 直接证明挂载卷失败的具体原因：ConfigMap 引用了不存在的键 |
| 2 | K8s State | kubernetes | Pod phase: `Pending`, container app status: `ContainerCreating` (fact-46054095b465, fact-a93fca118b11) | 确认 Pod 因挂载问题被阻断在启动前阶段，未进入运行态 |
| 3 | K8s Event | kubernetes | `Warning FailedMount ... Unable to attach or mount volumes: unmounted volumes=[input]` (fact-be159fd46224) | 辅助证明 kubelet 在长达 76 分钟内持续尝试挂载卷 `input` 均告失败 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (container=app, reason=ContainerCreating) = 1 (fact-75d05dfe3691) | 从监控指标维度印证容器当前处于等待启动状态 |

**证据印证说明：**
1. K8s Event 直接指出了失败机制（`configmap references non-existent config key: unavailable-key`），这与 Pod 状态（`Pending` / `ContainerCreating`）及 Metrics 中的等待原因完全一致。
2. 容器未进入运行状态，因此 Logging 和 Tracing 数据不适用（fact-86c016f70b3e 描述的事件也解释了无日志生成的原因）。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 缺失 Pod 卷定义中引用的 'unavailable-key' → kubelet 挂载卷 'input' 失败并持续重试 → Pod 'workload' 卡在 'Pending' 阶段，容器处于 'ContainerCreating' 状态 → 用户可见 Pod 无法就绪，无任何应用日志或流量
```

### 根因结论

**已确认的根因**：Pod `aiops-case-v05/workload` 的 Volume 挂载失败，导致容器无法启动。
*   **机制**：Pod 配置中卷 `input` 试图引用 ConfigMap `workload-input` 的键 `unavailable-key`，但该键在 ConfigMap 中不存在（依据证据 #1, fact-86c016f70b3e）。
*   **结果**：kubelet 在长达 78 分钟内持续因该挂载错误而阻塞（依据证据 #1, #3），导致容器 `app` 始终无法启动（依据证据 #2, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 15.1s
├─ 并发证据采集: 40.7s
│  └─ g1 aiops-case-v05/workload: 40.7s (Evidence 29.9s, RCA 10.7s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-volume-mount-failed
