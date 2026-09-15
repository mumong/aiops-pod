## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod spec中volume 'input'引用了不存在的Secret 'unavailable-input'且未声明Optional，导致MountVolume.SetUp持续失败，Pod无法调度容器启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod status: Pending; pod.phase: Pending (fact-id: fact-8ed69b2df6de) | 确认 Pod 整体处于未就绪状态 |
| 2 | K8s Event | kubernetes | FailedMount (fact-id: fact-6eb8bdd0575e): `MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` | 直接指出挂载失败原因：Secret 不存在 |
| 3 | K8s Event | kubernetes | FailedMount (fact-id: fact-d30873ac9da5): `timed out waiting for the condition` (unmounted volumes=[input]) | 确认挂载阻塞导致的状态停滞 |
| 4 | K8s State | kubernetes | container.waiting_reason: ContainerCreating (fact-id: fact-c457df51d315) | 确认容器处于启动等待阶段 |
| 5 | Metric | prometheus | kube_pod_container_status_waiting_reason: 1, reason=ContainerCreating (fact-id: fact-8de1b65cfc22) | 独立监控数据印证容器等待原因 |
| 6 | Metric | prometheus | kube_pod_container_status_restarts_total: 0 (fact-id: fact-3bb959a6d383) | 排除容器频繁重启导致的不稳定 |

**证据说明：**
Kubernetes 事件（#2, #3）与状态（#1, #4）高度一致，均指向因引用不存在的 Secret 导致卷挂载失败；Metric 数据（#5）独立确认了相同的等待原因（ContainerCreating）；重启计数为 0（#6）佐证故障发生在容器启动前的挂载阶段，排除应用层异常。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 中 volume 'input' 引用缺失的 Secret 'unavailable-input' 且未声明 Optional → Kubelet 尝试挂载该卷时找不到 Secret 对象，触发 FailedMount 警告 → 容器卷挂载依赖条件无法满足，容器状态停滞在 ContainerCreating → Pod 整体处于 Pending 状态
```

### 根因结论

**已确认根因**：Pod spec 中 volume `input` 引用了不存在的 Secret `unavailable-input`，且未配置 Optional 声明，导致 `MountVolume.SetUp` 持续失败，阻塞容器启动。

证据表明：
- Kubernetes 事件明确报错 `secret "unavailable-input" not found`（#2）；
- 容器一直卡在 `ContainerCreating` 状态（#4, #5）；
- 无重启记录，排除业务逻辑或健康检查失败因素（#6）；
- Metric 与 K8s State 互相印证（#1, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 19.5s
├─ 并发证据采集: 33.4s
│  └─ g1 aiops-case-v04/workload: 33.4s (Evidence 27.0s, RCA 6.2s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed
