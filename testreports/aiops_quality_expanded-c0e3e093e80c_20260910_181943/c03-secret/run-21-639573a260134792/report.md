## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod `aiops-case-v04/workload` 无法启动，因为其在 Pod Spec 中定义的 Volume `input` 引用了 Secret `unavailable-input`，但该 Secret 在 `aiops-case-v04` 命名空间中不存在（kubectl_get_by_kind_in_namespace 返回空），导致 Kubelet 挂载卷失败并无限期重试。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | kubernetes | volume `input` 引用了 Secret `unavailable-input` | 指出导致挂载失败的直接配置缺陷 |
| 2 | K8s Event | kubernetes | `FailedMount`: MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found | 确证 Secret 缺失导致挂载操作失败 |
| 3 | K8s Event | kubernetes | `FailedMount`: timed out waiting for the condition (x10 over 33m, x23 over 35m) | 证实重试机制持续触发且未成功 |
| 4 | K8s State | kubernetes | `app` 容器状态 `ContainerCreating`，Pod `phase` 为 `Pending` | 描述容器因前置条件不满足而处于阻塞状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` = 1 (fact-b093fb6300d0) | 确认等待原因为缺少前置挂载资源，与 K8s 状态一致 |

**证据关联说明**：
事件（#2）直接揭示了故障原因是 Secret `unavailable-input` 缺失，这解释了配置（#1）中的引用为何无法生效；重试事件（#3）与指标（#5）共同证实了 Kubelet 在 Pod 生命周期内不断尝试挂载但因条件不满足而无限期阻塞，最终导致容器始终处于 `ContainerCreating` 状态（#4）。

## 🎯 根因分析 · g1

### 因果链

```text
依赖的 Secret `unavailable-input` 缺失 → Kubelet 无法挂载 Volume `input` (FailedMount) → 容器 `app` 卡在 ContainerCreating 状态 → Pod 处于 Pending 状态，应用不可用
```

### 根因结论

已确认的根因为 **Secret `unavailable-input` 在 `aiops-case-v04` 命名空间中不存在**。Pod 的 Volume `input` 强依赖该 Secret，导致 Kubelet 挂载卷失败并持续重试（证据 #2, #3），致使容器无法完成初始化并永远停留在 `ContainerCreating` 状态（证据 #4, #5）。现有 K8s 状态与事件已构成完整且直接的证据链。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.8s
├─ 并发证据采集: 42.6s
│  └─ g1 aiops-case-v04/workload: 42.6s (Evidence 35.2s, RCA 7.2s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed
