## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod aiops-case-v04/workload 处于 ContainerCreating/Pending 状态，容器未启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount` : secret "unavailable-input" not found (fact-8d818e37c18b) | 直接指出挂载失败的具体原因 |
| 2 | K8s State | kubernetes | Pod phase: `Pending`, container.waiting_reason: `ContainerCreating` (fact-17b54ed96229, fact-b4e8d5e8ac82) | 确认 Pod 因依赖资源问题无法启动 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (reason=`ContainerCreating`) = 1 (fact-9d89f9c94ce2) | 独立确认容器处于等待状态 |

**证据说明：**
K8s Event 显示 kubelet 在尝试挂载卷 `input` 时，明确报告 Secret `unavailable-input` 不存在（fact-1）。该事件与 Event 中其他关于挂载超时的记录一致，直接解释了 K8s State 中容器卡在 `ContainerCreating` 且 Pod 处于 `Pending` 状态的原因（fact-2）。Prometheus 指标独立确认了该等待状态（fact-3），但未提供额外的机制信息。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 挂载配置引用不存在的 Secret 'unavailable-input' 且非可选 → kubelet 执行 MountVolume.SetUp 时检索 Secret 失败 → 卷挂载超时并持续报错 FailedMount → 容器状态卡在 ContainerCreating，Pod 处于 Pending
```

### 根因结论

已确认根因：Pod 定义中引用的 Secret `unavailable-input` 不存在，且挂载配置为非可选 (Optional: false)，导致 kubelet 挂载卷失败。

该根因直接支撑了现象：
- Secret 缺失事件 (fact-1) 解释了挂载失败。
- 挂载失败导致容器无法启动，从而表现为 `Pending`/`ContainerCreating` (fact-2)。

缺失决定性事实：确认 Secret `unavailable-input` 是意外删除还是存在拼写错误，需结合 GitOps 或部署历史确认。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 19.1s
├─ 并发证据采集: 35.6s
│  └─ g1 aiops-case-v04/workload: 35.6s (Evidence 27.6s, RCA 7.9s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed
