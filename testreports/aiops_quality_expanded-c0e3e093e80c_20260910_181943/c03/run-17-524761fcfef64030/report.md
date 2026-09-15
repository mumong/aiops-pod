## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod workload-5b5fc86c8c-xn974 stuck in ContainerCreating/Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Warning FailedMount (x35 over 55m): MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found | 核心证据：定位具体缺失的 ConfigMap |
| 2 | K8s Event | kubernetes | Warning FailedMount (x20 over 53m): unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition | 辅助证据：证明该卷挂载持续失败且无法启动 |
| 3 | K8s Config | kubernetes | container "app" resource_request: memory=8Mi, cpu=5m | 上下文：资源配额极低，排除因资源超限导致的调度阻塞 |
| 4 | K8s State | kubernetes | pod.status: Pending | 症状：Pod 处于等待状态，容器未进入运行态 |
| 5 | Metric | prometheus | kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1 | 独立验证：Prometheus 确认容器卡在容器创建阶段 |
| 6 | Metric | prometheus | kube_pod_status_phase{phase="Pending"} = 1 | 独立验证：确认 Pod 处于 Pending 阶段 |
| 7 | Metric | prometheus | kube_pod_container_status_restarts_total{container="app"} = 0 | 排除重启：容器尚未启动，无重启计数 |

**证据关联说明：**
Kubernetes 事件（#1）直接揭示了故障源为 `unavailable-config` 不存在；指标数据（#5, #6）从监控层独立确认了 Pod 处于 `ContainerCreating` 和 `Pending` 状态，与 K8s 事件中的 "timed out waiting"（#2）完全吻合；由于 Pod 始终未能启动，Logging 和 Tracing 维度无数据可采集。

## 🎯 根因分析 · g1

### 因果链

```text
缺失 ConfigMap 'unavailable-config' → 引用该 CM 的 'input' 卷挂载失败 → 阻塞容器启动流程 → Pod 保持 Pending 状态
```

### 根因结论

已确认根因：Pod `workload-5b5fc86c8c-xn974` 的卷定义 `input` 引用了不存在的 ConfigMap `unavailable-config`。

证据支撑：
- K8s 事件显示 `kubelet` 持续报告 `MountVolume.SetUp failed ... configmap "unavailable-config" not found`（#1）；
- 等待超时事件表明该挂载状态已持续 55 分钟（#2）；
- Metric 数据证实容器处于 `ContainerCreating` 且未重启（#5, #7），排除了应用逻辑错误导致的挂起。

该配置缺失导致 `kubelet` 无法完成卷挂载，直接造成 Pod 进入 `Pending` 状态，表现为 `ContainerCreating` 现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 21.2s
├─ 并发证据采集: 31.7s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 31.7s (Evidence 22.2s, RCA 9.4s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-volume-mount-failed
