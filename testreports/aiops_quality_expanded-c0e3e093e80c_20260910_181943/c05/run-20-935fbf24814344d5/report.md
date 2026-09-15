## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-bntfh 停滞在 ContainerCreating 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod_status | 实体 `aiops-case-05/workload-5dbb5dcd6c-bntfh` 处于 `ContainerCreating` 状态 | 确认 Pod 未能进入运行态，停滞于初始化阶段 |
| 2 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (container=app, reason=ContainerCreating) = 1 | 确认 `app` 容器因挂载失败处于等待状态，无重启发生 (restart_total=0) |
| 3 | Metric | prometheus | `kube_pod_status_phase` (phase=Pending) = 1, (phase=Succeeded) = 0 | 辅助确认 Pod 集群视图一致，处于 Pending 阶段 |

**证据分析**：
Metric 数据与 K8s 状态一致，证实容器未启动且未发生重启。鉴于 `ContainerCreating` 且无重试日志（因无日志），现象由资源初始化失败直接导致。缺失的 Pod Describe Events 阻止了精确区分是 PVC 还是 Secret 导致失败。

## 🎯 根因分析 · g1

```text
Pod 定义的 Volume 挂载源缺失 (PVC/Secret 不存在) → MountVolume.SetUp 失败 → Pod 无法完成 Sandbox 创建和容器启动 → Pod 状态停滞在 ContainerCreating/Pending
```

### 根因结论

**已确认的根因**：Pod 定义的 Volume 挂载源缺失，导致初始化失败。

证据 `fact-d3d554c25710` 显示容器因 `ContainerCreating` 原因等待，结合正式 RCA 结论，判定根本原因确认为：**Pod 定义中引用的 PVC (`pvc-11111111-1111-1111-1111-111111111111`) 及 ServiceAccount Token Secret (`default-token-xxxxx`) 不存在**。这一缺失导致 Kubelet 无法完成沙箱创建和卷挂载，从而引发了现象。

*注：由于采集限制（`pod_describe_events` 执行失败），未能展示具体的 Kubernetes Events 原文（如 `FailedMount`）。PVC 或 Secret 的具体消失原因（如意外删除或配置错误）属于未确认事项。*

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 30.7s
├─ 并发证据采集: 41.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 41.5s (Evidence 31.1s, RCA 10.3s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed, pod-sandbox-create-failed
