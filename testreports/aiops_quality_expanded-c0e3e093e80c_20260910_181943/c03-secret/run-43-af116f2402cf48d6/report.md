## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod aiops-case-v04/workload 卡在 ContainerCreating/Pending 状态，未进入运行 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` | 直接原因：集群日志明确指出版本卷挂载失败，因为目标 Secret 缺失 |
| 2 | K8s State | kubernetes | Pod 状态：`Pending`；容器 `app` 等待原因：`ContainerCreating` | 现象确认：Pod 无法进入运行状态，容器卡在创建阶段的挂载步骤 |
| 3 | K8s State | kubernetes | Pod 事件：`FailedMount`，累计失败 20+ 次 (57m) 及 35+ 次 (59m) | 失败持续性：确认故障非短暂网络延迟，而是持续存在的配置错误 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` = 1 | 外部观测印证：监控指标确认容器处于持续等待状态且重启次数为 0 |

**证据说明**：
Kubernetes 事件日志（证据 1、3）与 K8s 状态（证据 2）在“挂载卷失败”这一机制上高度一致，共同解释了 Pod 为何卡在 `Pending` 状态。Prometheus 指标（证据 4）提供了无重启（重启次数为 0）且状态持续为 `ContainerCreating` 的外部佐证，排除了容器崩溃重启或网络抖动导致的问题。日志与事件记录中关于 `secret "unavailable-input" not found` 的信息是决定性的，无需 Tracing 数据即可闭环。

## 🎯 根因分析 · g1

```text
Secret 'unavailable-input' 不存在 → 容器卷挂载配置引用该缺失 Secret (Optional: false) → kubelet 尝试挂载卷时永久失败 (FailedMount) → Pod 卡在 ContainerCreating/Pending 状态，无法启动容器
```

### 根因结论

**已确认的根因**：Pod `aiops-case-v04/workload` 的容器 `app` 引用了不存在的 Secret `unavailable-input` 作为 Volume `input`，且该引用未配置为可选。这导致 `kubelet` 在初始化阶段因无法获取 Secret 数据而持续挂载失败，阻止了容器的创建与启动（详见证据 1、2）。

**关于未决项**：
现有证据足以解释“Pod 为何启动失败”，但无法回答“为什么 Secret 不存在”（可能未被创建或已被误删），也无法确认集群内是否存在其他同样依赖该 Secret 的受影响 Pod。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 33.7s
├─ 并发证据采集: 41.3s
│  └─ g1 aiops-case-v04/workload: 41.3s (Evidence 30.8s, RCA 10.4s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-imagepull-failed, pod-sandbox-create-failed
