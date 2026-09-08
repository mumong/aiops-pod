## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod workload-5b5fc86c8c-2xgjz 处于 ContainerCreating 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `event.message` | `FailedMount 90s (x18 over 21m) ... MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 核心证据，直接指出 ConfigMap 缺失导致挂载失败 |
| 2 | K8s Event | `event.message` | `Unable to attach or mount volumes: unmounted volumes=[input]...` | 补充证据，确认 volume 挂载状态异常 |
| 3 | K8s State | `pod.condition` | `ContainersReady: False (reason: ContainersNotReady)` | 现象证据，确认 Pod 容器未就绪 |
| 4 | K8s State | `container.waiting_reason` | `ContainerCreating` | 现象证据，确认 Pod 卡在创建阶段 |
| 5 | Metric | `kube_pod_container_status_waiting_reason` | `value: 1, labels: {container: "app", reason: "ContainerCreating"}` | 独立验证，Prometheus 指标证实等待原因为创建中 |

**证据关联说明**：
- 证据 1（K8s Event）与证据 5（Metric）互相印证：事件日志明确指出 `FailedMount` 的根源是 `configmap "unavailable-config" not found`，而指标数据证实容器确实处于由该原因导致的等待状态。
- 证据 2 进一步确认了该 Volume 未能成功挂载的事实。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 缺失 → Volume 'input' 挂载失败 (FailedMount) → Pod 卡在 ContainerCreating 状态 → 服务不可用
```

### 根因结论

已确认的根因是 **ConfigMap 'unavailable-config' 在当前命名空间中不存在**。

由于 Pod 定义中的 volume `input` 未配置为可选挂载，kubelet 在尝试挂载该 Volume 时找不到对应的 ConfigMap，导致 `MountVolume.SetUp` 失败并报错（证据 1、2）。这一机制性阻塞使得容器无法完成初始化，Pod 状态被锁定在 `ContainerCreating`（证据 3、4、5），从而导致服务不可用。现有证据充分，诊断发布条件满足。

---

## 📊 性能统计

```text
├─ 总耗时: 9.6m
├─ 问题定位: 18.1s
├─ 并发证据采集: 549.4s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 549.4s (Evidence 542.1s, RCA 7.2s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-volume-mount-failed
