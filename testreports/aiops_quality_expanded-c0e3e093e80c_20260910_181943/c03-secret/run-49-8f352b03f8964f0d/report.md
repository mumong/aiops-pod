## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod aiops-case-v04/workload 持续处于 ContainerCreating/Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `FailedMount  3m30s (x40 over 68m) ... MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` | 核心根因证据：明确指出因 Secret 缺失导致 Volume 挂载持续失败 |
| 2 | K8s Event | kubelet | `FailedMount  7m45s (x27 over 66m) ... unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition` | 辅助证据：确认挂载卷状态异常且超时，与事实 1 共同确立故障现象 |
| 3 | K8s Config | Pod Spec | `volume "input"` 引用了 `secret "unavailable-input"` | 根因映射：建立卷与缺失资源的引用关系，确认故障源头 |
| 4 | K8s State | Pod Status | `phase: Pending` | 症状验证：Pod 因依赖资源缺失而卡在初始化阶段 |

证据 1 与 2 相互印证了 kubelet 对 `input` 卷的持续挂载失败；证据 3 解释了为何会报 `secret "unavailable-input" not found`，直接锁定了根因。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'unavailable-input' 缺失 → Kubelet 挂载卷失败(FailedMount) → Pod 无法完成初始化 → 持续处于 ContainerCreating/Pending 状态
```

### 根因结论

**已确认的根因**：
Pod `aiops-case-v04/workload` 处于 `Pending` 状态且容器无法启动，根本原因是 Pod Spec 中的 Volume `input` 引用了不存在的 Secret `unavailable-input` [证据 3]。
Kubelet 在尝试挂载该卷时持续报错 `secret "unavailable-input" not found` [证据 1]，并伴随超时警告 [证据 2]。这种挂载失败导致 Pod 卡在初始化阶段，表现为 `ContainerCreating` [证据 4]。

---

## 📊 性能统计

```text
├─ 总耗时: 57.9s
├─ 问题定位: 12.2s
├─ 并发证据采集: 38.4s
│  └─ g1 aiops-case-v04/workload: 38.4s (Evidence 30.1s, RCA 8.2s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed
