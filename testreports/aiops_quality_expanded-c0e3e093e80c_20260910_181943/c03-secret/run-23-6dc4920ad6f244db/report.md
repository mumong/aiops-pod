## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod workload in aiops-case-v04 is stuck in ContainerCreating/Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` (fact-258ab1cb9337) | 核心根因证据：明确报错 Secret 缺失导致挂载失败 |
| 2 | K8s Event | kubernetes | `Warning FailedMount ... Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition` (fact-17e97072e3f8) | 佐证机制：确认挂载动作因 volume 条件未满足而超时 |
| 3 | K8s State | kubernetes | `pod.phase: Pending` (fact-725956be3194) | 现象证据：Pod 因资源/依赖未就绪处于挂起状态 |
| 4 | K8s State | kubernetes | `pod.condition.ContainersReady: False, reason: ContainersNotReady` (fact-7385412b46cb) | 现象证据：确认容器未进入 Ready 状态 |
| 5 | K8s State | kubernetes | `container.waiting_reason: ContainerCreating` (fact-31c26ed34658) | 现象证据：容器处于等待就绪的中间状态 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason[reason="ContainerCreating"] = 1` (fact-0e9f3a9a30a3) | 现象佐证：监控确认容器持续处于 ContainerCreating 状态 |

**证据印证**：
Kubernetes 事件直接指出了失败的具体对象是名为 `unavailable-input` 的 Secret，且错误原因为 `not found` (证据 #1, #2)。Pod 的状态数据与指标数据 (证据 #3-6) 一致表明 Pod 停滞在 `ContainerCreating` 和 `Pending` 阶段，未发生任何重试或重启 (restart_count: 0)，这符合因静态配置缺陷（Secret 缺失）导致的不可恢复故障特征。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 的 'input' Volume 引用了不存在的 Secret 'unavailable-input' (Optional: false)
→ Kubelet 挂载卷时因 Secret 缺失返回 "not found" 错误 (FailedMount)
→ Pod 因依赖卷挂载失败被调度器或 Kubelet 判定为不可启动 (Pending/ContainerCreating)
→ 用户/集群观测到该 Pod 持续停滞，无法进入 Running 状态
```

### 根因结论

**已确认的根因：Pod `aiops-case-v04/workload` 声明了对 Secret `unavailable-input` 的挂载依赖，但该 Secret 在集群中不存在。**

根据事实 `fact-258ab1cb9337`，Kubelet 明确记录了 `secret "unavailable-input" not found` 的挂载失败事件。由于该 Volume 配置中 `Optional` 标志为 `false`（隐含在 `not found` 导致阻断的行为中），Kubelet 无法启动容器，导致 Pod 停留在 `ContainerCreating` 状态。

相关证据编号：
- 挂载失败具体原因：`fact-258ab1cb9337`, `fact-17e97072e3f8`
- Pod 持续停滞状态：`fact-725956be3194`, `fact-31c26ed34658`
- 监控状态佐证：`fact-0e9f3a9a30a3`

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.0s
├─ 并发证据采集: 34.9s
│  └─ g1 aiops-case-v04/workload: 34.8s (Evidence 27.0s, RCA 7.7s)
└─ 汇总总结: 12.2s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed
