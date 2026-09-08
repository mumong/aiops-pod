## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod workload-5b5fc86c8c-2xgjz 处于 ContainerCreating/Pending 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount` (fact-8936aabb887c): `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (x40 over 68m) | 直接指向挂载失败的根本原因，确认为 ConfigMap 缺失 |
| 2 | K8s Event | kubernetes | `FailedMount` (fact-f8727edac180): `Unable to attach or mount volumes: unmounted volumes=[input]... timed out waiting for the condition` (x27 over 66m) | 辅助证据，确认挂载超时现象 |
| 3 | K8s State | kubernetes | 状态 (fact-20c6fe996fb1, fact-d4e7356a4a8d): Pod `phase: Pending`，容器 `app` 处于 `ContainerCreating` (fact-f6b75818dc94) | 描述故障现场的具体状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (fact-dfdf8846d5ee): `1` (reason: `ContainerCreating`) | 独立验证 Pod 持续卡在创建阶段 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total` (fact-10f78691ea16): `0` | 排除因重启或 CrashLoopBackOff 导致的故障可能 |

**证据综述：**
Kubernetes 事件日志（#1, #2）提供了决定性的因果线索，明确指出 `configmap "unavailable-config" not found` 导致了 `FailedMount`。Metrics（#4, #5）与 K8s 状态（#3）相互印证，确认了该 Pod 在长时间内持续处于 `Pending` 和 `ContainerCreating` 状态，且未发生容器重启。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用了不存在的 ConfigMap 'unavailable-config' → Kubelet 挂载 Volume 校验失败 (ConfigMap not found) → 触发 FailedMount 事件，Pod 无法进入 Running 状态 → Pod 卡在 Pending/ContainerCreating 状态
```

### 根因结论

已确认根因为：**Pod Spec 中引用了一个不存在的 ConfigMap `unavailable-config`**。

证据表明，Kubelet 在尝试挂载名为 `input` 的 Volume 时，发现指定的 ConfigMap 不存在，导致挂载操作失败（详见证据 #1 `fact-8936aabb887c`）。这一上游原因直接导致了 `FailedMount` 事件的持续触发，使得容器无法启动，进而表现为 Pod 长期处于 `Pending` 状态（详见证据 #3 `fact-20c6fe996fb1`, #4 `fact-dfdf8846d5ee`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 21.2s
├─ 并发证据采集: 41.8s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 41.8s (Evidence 33.0s, RCA 8.7s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-volume-mount-failed
