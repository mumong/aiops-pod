## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload stuck in Pending/ContainerCreating state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod phase: `Pending`, status: `ContainerCreating` (app), restarts: `0` | 确证容器启动停滞，处于初始异常阶段 |
| 2 | K8s Event | Kubernetes | `FailedMount` (x7 over 14m): `timed out waiting for the condition` | 指示挂载过程长期失败并超时 |
| 3 | K8s Event | Kubernetes | `FailedMount` (x16 over 16m): `MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` | 直接定位挂载失败的底层资源错误 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` = `1` (10:32:43Z) | 独立观测证实容器处于等待状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = `0` | 排除 CrashLoopBackOff 或频繁重启干扰 |

**证据总结：**
Kubernetes Event 明确指出 `MountVolume.SetUp` 失败且错误详情为引用了不存在的 ConfigMap key（`unavailable-key`），这是导致挂载超时（Event #2）的直接原因。Metrics 数据（#4, #5）从时间序列上交叉验证了容器确实长期处于 `ContainerCreating` 状态且无重启，与事件发生的时间跨度一致。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 缺失 key 'unavailable-key' → kubelet 挂载体积 'input' 失败 → 触发 FailedMount 事件并进入挂载超时 → 容器 'app' 停滞在 ContainerCreating/Pending 状态
```

### 根因结论

已确认根因为：Volume `input` 引用了 ConfigMap 中不存在的数据键 `unavailable-key`。

该配置错误导致 `kubelet` 无法完成 `MountVolume.SetUp` 操作，进而引发了持续的 `FailedMount` 警告事件（证据 #2, #3）。由于挂载是容器启动的前置条件，Pod 被锁定在 `Pending` 状态（证据 #1），等待中的指标确认了这一状态长期存在（证据 #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.9s
├─ 并发证据采集: 38.4s
│  └─ g1 aiops-case-v05/workload: 38.4s (Evidence 28.1s, RCA 10.2s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-config-error, pod-pending-unschedulable, pod-volume-mount-failed
