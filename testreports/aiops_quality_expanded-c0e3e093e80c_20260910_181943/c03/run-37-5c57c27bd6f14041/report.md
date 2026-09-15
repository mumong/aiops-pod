## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | workload-5b5fc86c8c-xn974 ContainerCreating |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.waiting_reason: ContainerCreating (fact-11049bfd4b42) | 确认容器因卷挂载受阻而滞留等待 |
| 2 | K8s Event | kubernetes | FailedMount: MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found (fact-c2beac52b620) | 直接指出失败机制是 ConfigMap `unavailable-config` 缺失 |
| 3 | K8s Event | kubernetes | FailedMount: timed out waiting for the condition (fact-c53a4730b824) | 确认挂载操作持续失败导致 Pod 无法继续调度 |
| 4 | K8s State | kubernetes | pod.phase: Pending (fact-42408d47f05b) | 确认 Pod 处于调度完成但运行前置校验未通过的锁定状态 |
| 5 | Metric | prometheus | kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1 (fact-c8b4a76aa8f7) | 独立观测到 Pod 处于 Waiting 状态且原因为 ContainerCreating |
| 6 | Metric | prometheus | kube_pod_status_phase{phase="Pending"} = 1 (fact-dc7fd9cb5d72) | 独立观测到 Pod 生命周期阶段被锁定为 Pending |

**证据链说明**：
K8s Event (`#2`) 提供了唯一的根因诊断依据（缺少 ConfigMap），K8s State (`#1`, `#4`) 与 Metric (`#5`, `#6`) 分别从 Pod 运行状态和生命周期阶段两个维度交叉印证了故障现象的一致性。Logging 和 Tracing 因 Pod 尚未启动且 IP 为空而无法采集，但现有的 K8s 与 Metrics 事实已构成完整闭环，无需依赖它们即可定损。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap `unavailable-config` 不存在 → Kubelet 挂载卷失败 → Pod 状态锁定为 Pending / ContainerCreating → 应用服务不可用
```

### 根因结论

**已确认根因**：Pod `aiops-case-03/workload-5b5fc86c8c-xn974` 定义了一个名为 `input` 的卷，该卷引用了 ConfigMap `unavailable-config`，但在该命名空间中不存在此资源（依据 `#2` Event）。这导致 Kubelet 的 `MountVolume.SetUp` 阶段报错并超时，Pod 被锁定在 `Pending` 阶段无法进入 `Running` 状态（依据 `#1`, `#4`, `#5`, `#6`）。

**证据不足**：现有证据已充分解释 Pod 为何处于 `ContainerCreating` 等待态。关于“为何该 ConfigMap 缺失”（例如是未部署还是被误删）目前未确认，因为未采集集群级别的 ConfigMap 列表进行历史比对。

---

## 📊 性能统计

```text
├─ 总耗时: 9.7m
├─ 问题定位: 20.7s
├─ 并发证据采集: 548.5s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 548.5s (Evidence 539.9s, RCA 8.5s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-volume-mount-failed
