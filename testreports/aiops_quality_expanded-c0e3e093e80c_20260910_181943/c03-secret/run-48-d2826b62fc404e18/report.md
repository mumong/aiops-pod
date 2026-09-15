## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod spec 中引用了不存在的 Secret 'unavailable-input' 且 Optional 为 false，导致 kubelet 挂载 Volume 失败，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-cdad2954f18f` | `Warning FailedMount 2m33s (x40 over 67m) kubelet MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` | 证实挂载失败及缺失资源名 |
| 2 | K8s Event | `fact-e4f90296f783` | `Warning FailedMount 6m48s (x27 over 65m) kubelet Unable to attach or mount volumes: unmounted volumes=[input]...` | 佐证挂载失败的持续性现象 |
| 3 | Metric | `fact-fe5fc54b87d2` | `kube_pod_container_status_waiting_reason=1` (reason=`ContainerCreating`) | 量化指标确认容器等待状态 |
| 4 | K8s State | `fact-08689c8efa98` | `container.restart_count: 0` | 确认容器未经历重启循环，非运行时异常 |

事件日志 `fact-cdad2954f18f` 提供了根因的直接证据（Secret `unavailable-input` 不存在），Metric `fact-fe5fc54b87d2` 独立证实了 Pod 处于 `ContainerCreating` 等待状态。容器重启次数为 `0`（`fact-08689c8efa98`）排除了因 OOM 或崩溃导致的启动失败，进一步锁定了启动前挂载阶段的问题。

## 🎯 根因分析 · g1

### 因果链
```text
Pod spec 引用不存在的 Secret 'unavailable-input' 且 Optional=false → kubelet MountVolume.SetUp 失败 → 容器无法启动(Pending/Waiting) → 现象为 Pod 状态不健康且重启次数为0
```

### 根因结论
确认根因为 **Pod Spec 引用了不存在的 Secret 'unavailable-input'**。

该引用导致 kubelet 在挂载卷阶段失败（证据 1, 2），直接引发容器无法启动，表现为 `ContainerCreating` 状态及等待原因（证据 3）。由于故障发生在容器启动之前，未产生任何运行时异常，故重启次数为 0（证据 4）。现有 Kubernetes 状态与事件证据充分，根因已确认。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 31.2s
├─ 并发证据采集: 35.1s
│  └─ g1 aiops-case-v04/workload: 35.1s (Evidence 28.3s, RCA 6.4s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-imagepull-failed, pod-volume-mount-failed
