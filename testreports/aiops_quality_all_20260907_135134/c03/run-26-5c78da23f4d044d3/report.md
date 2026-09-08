## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod YAML中定义的Volume 'input' 引用了不存在的ConfigMap 'unavailable-config'（Optional: false），导致kubelet挂载卷永久失败，Pod被卡在Pending/ContainerCreating状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod phase: Pending; container.waiting_reason: ContainerCreating | 确认应用容器 `app` 处于启动前阻塞阶段，尚未运行 |
| 2 | K8s Event | kubernetes | `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (fact-63293e885cdf) | 直接定位挂载失败的具体资源缺失原因 |
| 3 | K8s Event | kubernetes | `timed out waiting for the condition` for unmounted volumes=[input] (fact-23d3e5b75b0d) | 证实 kubelet 在长达 44 分钟内反复重试挂载失败 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` (fact-e9f8d3ed29d7) | 独立观测验证容器处于 Waiting 状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total = 0` (fact-9fdbbe21a68a) | 证实容器从未启动过，不存在 CrashLoopBackOff 等运行时问题 |

**证据关联说明：**
Kubernetes 事件（#2）明确指缺少的配置对象为 `configmap "unavailable-config"`，且 Pod 处于 `Pending` 状态（#1），这与 Metrics 中观测到的 `ContainerCreating` 等待状态（#4）及 `restart_count=0`（#5）完全一致，证明故障发生在调度后的挂载阶段，而非容器启动后。

## 🎯 根因分析 · g1

### 因果链

```text
引用不存在的 ConfigMap 'unavailable-config' → kubelet 挂载卷永久失败 → 容器无法启动 → Pod 卡在 Pending/ContainerCreating 状态
```

### 根因结论

已确认的根因为 **Pod YAML 定义引用了缺失的依赖资源**，具体由 `configmap "unavailable-config"` 不存在引起。由于挂载操作在容器启动前发生且失败，Pod 被永久阻塞在 `Pending` 状态，导致应用无法运行且无重启记录。证据支持充分。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.3s
├─ 并发证据采集: 39.2s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 39.2s (Evidence 33.7s, RCA 5.5s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-imagepull-failed
