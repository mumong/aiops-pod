## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod workload (aiops-case-v05) is stuck in phase=Pending / ContainerCreating state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Phase: Pending, Reason: ContainerCreating | 确认 Pod 处于初始化停滞状态 |
| 2 | K8s Event | Kubernetes | `FailedMount`: configmap references non-existent config key: unavailable-key | 直接指出挂载失败的配置原因 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` = 1 | 从监控侧印证 Pod 未进入运行态 |
| 4 | Metric | Prometheus | `kube_pod_status_phase{phase="Pending"}` = 1 | 从监控侧印证 Pod 生命周期卡住 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 | 排除容器启动后的异常循环重启 |

**证据关联说明：**
事件 `FailedMount`（事实 #2）直接解释了状态为 `ContainerCreating`（事实 #1）的根本原因——无法挂载 volume。Metric 数据（事实 #3、#4、#5）从指标层面交叉验证了该 Pod 长时间停留在初始化阶段且未发生重启，确认故障处于持续阻塞状态而非瞬时波动。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 引用了不存在的 ConfigMap key -> kubelet 挂载卷时校验失败 -> 容器无法创建 -> Pod 无限期处于 Pending/ContainerCreating 状态
```

### 根因结论

**已确认的根因：配置缺失导致的卷挂载失败。**

Pod `aiops-case-v05/workload` 的配置文件引用了 ConfigMap `workload-input` 中的 key `unavailable-key`，但该 key 实际上并不存在（证据 #2, 事实 `fact-a9af185d85b5`）。这一缺失导致 kubelet 在执行 `MountVolume.SetUp` 时反复失败，致使容器 `app` 无法完成启动流程，进而使 Pod 一直停留在 `ContainerCreating` 状态（证据 #1, #3, 事实 `fact-8df28ffaa869`, `fact-e0c68d5d9379`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 24.0s
├─ 并发证据采集: 58.8s
│  └─ g1 aiops-case-v05/workload: 58.8s (Evidence 51.4s, RCA 7.2s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-sandbox-create-failed
