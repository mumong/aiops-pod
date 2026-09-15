## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod workload in aiops-case-v05 is stuck in ContainerCreating/Pending state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount`: `configmap references non-existent config key: unavailable-key` (fact-ed377260858b) | 证实 Pod 挂载卷失败的具体技术原因 |
| 2 | K8s Event | kubernetes | `FailedMount`: `timed out waiting for the condition` (fact-578d23206d09) | 证实挂载操作的持续阻塞状态 |
| 3 | K8s State | kubernetes | `Pod status`: `Pending` (fact-6b11d4686f3a) | 确认 Pod 当前运行阶段为等待挂载完成 |
| 4 | K8s Event | kubernetes | `Warning  FailedMount  83s (x31 over 69m)` (fact-578d23206d09) | 证明异常持续发生近 1 小时，非瞬态问题 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` value=1 (fact-84face696793) | 度量层面确认容器持续处于创建等待阶段 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total` value=0 (fact-4fbb3c59a8aa) | 排除应用进程崩溃重启引发的故障可能 |
| 7 | K8s Config | kubernetes | Container `app` resource requests/limits defined (fact-853d52daa060 等) | 确认资源配置正常，资源限制与挂载失败无直接关联 |

**证据互证分析**
- 证据 1 与 2 构成直接因果链：ConfigMap 键缺失导致卷挂载失败（`MountVolume.SetUp failed`）。
- 证据 3、4 与 5 互相印证：Pod 状态（Pending）与容器等待原因（ContainerCreating）一致，且错误持续超过 69 分钟，排除了短暂网络抖动。
- 证据 6 结合证据 3 排除了应用逻辑错误，确认故障发生在容器启动前的基础环境准备阶段。
- Logging/Tracing 维度标记为 `not_applicable`，因容器未启动无法产生相关数据，这与 K8s 事件显示的底层挂载失败逻辑一致。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 卷 'input' 引用了不存在的键 'unavailable-key' → Kubelet 挂载卷失败 (MountVolume.SetUp failed) → Pod 卡在 Pending 状态，原因 ContainerCreating → 应用无法启动
```

### 根因结论

已确认的根因为：**Pod 的 Volume 配置错误，引用了目标 ConfigMap 中不存在的 Key (`unavailable-key`)。**

该配置错误导致 Kubelet 无法完成 `input` 卷的挂载工作，从而触发 `FailedMount` 事件并持续重试，致使 Pod 永远停留在 `Pending` 阶段，容器无法启动（证据 #1, #2, #3, #4, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.6s
├─ 并发证据采集: 46.5s
│  └─ g1 aiops-case-v05/workload: 46.5s (Evidence 38.9s, RCA 7.4s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-volume-mount-failed, pod-sandbox-create-failed
