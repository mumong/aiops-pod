## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod workload-5b5fc86c8c-2xgjz 处于 ContainerCreating/Pending 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | phase: Pending; status: Pending; condition Ready=False (ContainersNotReady) | 确认 Pod 未进入运行阶段 |
| 2 | K8s Event | kubernetes | Warning FailedMount: "MountVolume.SetUp failed for volume \"input\" : configmap \"unavailable-config\" not found" | 直接揭示 Pod 挂起的确切原因是缺少配置对象 |
| 3 | K8s Event | kubernetes | Warning FailedMount: "timed out waiting for the condition" | 反映 kubelet 持续重试挂载该卷导致状态卡滞 |
| 4 | K8s State | kubernetes | container.waiting_reason: ContainerCreating | 验证 Pod 处于启动前的等待状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` = 1 | 独立观测确认容器未启动 |
| 6 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"}` = 1 | 独立观测确认 Pod 未上线 |

当前异常由 Kubernetes 控制面与 Node 组件直接记录。Metric 与 K8s Event 相互印证了 `ContainerCreating` 与 `Pending` 的停滞状态，而 Event 中的 `FailedMount` 错误明确指向了具体的资源依赖问题。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用不存在且不可选的 ConfigMap 'unavailable-config' → kubelet 挂载卷查找失败 → 挂载持续超时导致 Waiting/ContainerCreating → Pod 状态保持 Pending，服务不可用
```

### 根因结论

已确认的根因是：Pod 定义中引用了名为 `unavailable-config` 的 ConfigMap，但由于该 ConfigMap 不存在且挂载配置为必填（非可选），kubelet 在 `MountVolume.SetUp` 阶段无法完成卷挂载。这一资源依赖缺失导致 Pod 无法进入 `Running` 状态，从而表现服务不可用（证据 1-4 证实）。

---

## 📊 性能统计

```text
├─ 总耗时: 54.0s
├─ 问题定位: 13.5s
├─ 并发证据采集: 33.2s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 33.2s (Evidence 25.8s, RCA 7.4s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-volume-mount-failed
