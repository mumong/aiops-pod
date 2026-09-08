## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod配置引用了不存在的ConfigMap 'unavailable-config'，导致Volume挂载失败，容器卡在ContainerCreating状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount` (fact-80274ae0a2f5): `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 明确根因：挂载卷因 ConfigMap 缺失而失败 |
| 2 | K8s State | kubernetes | `ContainerCreating` (fact-3eb34081a1b6): 容器 `app` 卡在创建中 | 直接现象证据 |
| 3 | K8s State | kubernetes | `Pending` (fact-63edcd22264f, fact-a0ce857a9176): Pod 处于待处理状态 | 全局阶段证据 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (fact-5070c6333cc5): 容器处于 `ContainerCreating` 等待状态 | 确认当前状态，佐证 K8s 状态 |
| 5 | Metric | prometheus | `kube_pod_status_phase=1` (fact-009a7981ea01): Pod 处于 `Pending` 阶段 | 确认全局状态 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total=0` (fact-3636b1cfd608): 重启次数为 0 | 排除应用层启动失败或 OOM 重启 |
| 7 | Topology | kubernetes | Resource Limit: 32Mi Memory / 50m CPU (fact-1b2fa7c46268); Resource Request: 8Mi Memory / 5m CPU (fact-1e08798dd6d4) | 排除资源不足或超卖问题 |

**证据关系说明：**
Kubernetes Event (fact-80274ae0a2f5) 中的 `FailedMount` 错误原文是判定根因的决定性证据；Metric 数据 (fact-5070c6333cc5, fact-009a7981ea01) 从时间序列维度确认了 Pod 与容器当前所处的 `ContainerCreating` 和 `Pending` 状态与 K8s 状态事实一致；资源配置事实 (fact-1b2fa7c46268, fact-1e08798dd6d4) 证明了集群资源充足，隔离了资源配额问题。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 缺失 → Kubelet 执行 MountVolume.SetUp 失败 → Pod 无法挂载 'input' 卷 → 容器 'app' 卡在 ContainerCreating 状态，Pod 进入 Pending 状态
```

### 根因结论

**已确认根因**：Pod `workload-5b5fc86c8c-zz82w` 的卷配置引用了名为 `unavailable-config` 的 ConfigMap，但该资源不存在。

这一缺失直接导致 kubelet 在挂载卷 `input` 时抛出 `MountVolume.SetUp failed` 错误（事实编号 fact-80274ae0a2f5），进而使得容器无法启动（事实编号 fact-3eb34081a1b6）。这一故障链排除了应用层问题、资源不足或其他网络问题。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 49.1s
├─ 并发证据采集: 61.3s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 61.3s (Evidence 57.2s, RCA 3.9s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed, pod-sandbox-create-failed
