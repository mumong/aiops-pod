## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod 的 Volume `input` 引用了不存在的 ConfigMap `unavailable-config`，导致 kubelet MountVolume 失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `Warning FailedMount 55s (x15 over 15m) kubelet MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 核心证据：直接指出 Volume 挂载失败的具体原因是引用了不存在的 ConfigMap |
| 2 | K8s Event | `kubernetes` | `Warning FailedMount 111s (x6 over 13m) kubelet Unable to attach or mount volumes: unmounted volumes=[input]` | 核心证据：确认故障具有持续性，自 111s 起持续发生 |
| 3 | K8s State | `kubernetes` | `container.waiting_reason: {"container": "app", "reason": "ContainerCreating"}` | 支撑证据：确认容器因挂载失败而处于等待状态 |
| 4 | K8s State | `kubernetes` | `pod.status: {"status": "Pending"}` | 支撑证据：确认 Pod 整体卡在调度后的挂载阶段，未进入运行状态 |

> **证据关联说明：**
> 证据 1 与证据 2 在时间维度（15m/13m 窗口）与状态维度（FailedMount）上互为印证，排除偶发性故障；证据 1 与证据 3 形成因果闭环：配置缺失导致挂载失败（证据1），进而导致容器进入 ContainerCreating 等待状态（证据3）。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap `unavailable-config` 缺失 → Kubelet MountVolume 失败 (证据1/2) → 容器持续等待启动 (证据3) → Pod 状态为 Pending
```

### 根因结论

已确认根因：Pod 定义中引用的 Volume `input` 绑定了不存在的 ConfigMap `unavailable-config`。该配置缺失导致 kubelet 无法完成挂载，直接引发 `FailedMount` 事件，使得容器无法进入运行状态。

---

## 📊 性能统计

```text
├─ 总耗时: 9.7m
├─ 问题定位: 543.7s
├─ 并发证据采集: 32.9s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 32.9s (Evidence 28.6s, RCA 4.1s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-volume-mount-failed
