## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-zz82w 卡在 ContainerCreating 状态（Pending），容器未启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (fact-ea8718b5e421) | 证实容器挂载卷的直接错误原因 |
| 2 | K8s State | kubernetes | Pod 状态: `Pending` (fact-d3510998b615) | 描述 Pod 当前的停滞状态 |
| 3 | K8s State | kubernetes | 容器状态: `ContainerCreating` (fact-dbc7eeb6296b) | 说明应用容器卡在初始化阶段，未进入 Running |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值: `1` (labels: `reason=ContainerCreating`, fact-035e9227630b) | 监控层面确认容器处于等待挂载状态 |
| 5 | K8s Config | kubernetes | Pod 引用 Volume `input` (来自事件上下文 fact-ea8718b5e421) | 标识出发生故障的具体 Volume 名称 |

**证据说明：**
Kubernetes 事件明确指出 Volume `input` 挂载失败的原因是 ConfigMap `unavailable-config` 缺失。这一配置错误直接导致容器处于 `ContainerCreating` 状态并拒绝启动（Fact 1, 2, 3），且监控数据（Fact 4）在指标层面印证了该等待状态。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 不存在 → MountVolume.SetUp 失败 → Pod 无法完成卷挂载 → 容器保持 ContainerCreating 状态
```

### 根因结论

已确认的根因是：Pod 定义中 Volume `input` 引用了不存在的 ConfigMap `unavailable-config`。
该配置错误导致 kubelet 在尝试挂载卷时返回 `configmap "unavailable-config" not found` 错误（证据编号：1）。由于无法完成必要的卷挂载，容器进程无法启动，从而使得 Pod 停滞在 `ContainerCreating` 状态（证据编号：2, 3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 28.3s
├─ 并发证据采集: 47.0s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 47.0s (Evidence 38.1s, RCA 8.7s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed
