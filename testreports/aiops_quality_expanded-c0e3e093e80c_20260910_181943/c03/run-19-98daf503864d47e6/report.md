## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | aiops-case-03/workload-5b5fc86c8c-xn974 pod status: ContainerCreating/Pending; volume 'input' mount failure |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-03/workload-5b5fc86c8c-xn974` 状态：`Pending`，重启次数：0 | 确认应用容器未进入运行态，属于启动阻断 |
| 2 | K8s Event | kubernetes | `FailedMount` (x20 over 55m) `timed out waiting for the condition` | 证明 Kubelet 挂载卷时反复超时重试 |
| 3 | K8s Event | kubernetes | `FailedMount` (x35 over 57m) `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 直接指明失败原因为 ConfigMap 缺失 |
| 4 | K8s Config | kubernetes | 资源请求：CPU `5m` / 内存 `8Mi`；限制：CPU `50m` / 内存 `32Mi` | 排除因资源不足（CPU/Memory Limit/Request）导致调度失败的常见场景 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 `1`，标签 reason=`ContainerCreating` | 从时序数据确认 Pod 处于等待阶段，与 Event 状态相互印证 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total` 值为 `0` | 确认 Pod 从未成功启动，排除了因运行中崩溃导致的现象 |
| 7 | Metric | prometheus | `kube_pod_status_phase` 标签 phase=`Pending` 值为 `1`，`Unknown` 值为 `0` | 确认 Pod 始终停留在 Pending 阶段，未转为 Unknown |

证据 2 和 3 通过 `FailedMount` 事件及错误信息中的 `configmap "unavailable-config" not found`，确立了 ConfigMap 缺失是导致挂载失败的直接原因。证据 4 证明资源请求极低，佐证了并非资源调度瓶颈，而是存储依赖问题。证据 1、5、6 和 7 从 Pod 状态、等待原因和重启计数多个维度确认了该 Pod 长期处于无法启动的 Pending 状态，未发生后续生命周期行为。

## 🎯 根因分析 · g1

```text
ConfigMap 'unavailable-config' 缺失（原因未确认） → Kubelet 尝试挂载绑定该 ConfigMap 的 'input' 卷（Optional=false） → 挂载反复失败并超时 → Pod 维持在 Pending/ContainerCreating 状态
```

**根因结论：**
已确认根因是 Pod 的 `input` 卷引用的 ConfigMap `unavailable-config` 不存在。
- **机制印证**：根据证据 2 和 3，Kubelet 因找不到 ConfigMap 而持续报 `FailedMount` 错误，导致 Pod 陷入等待状态。证据 4 排除资源限制干扰，证据 1、5、6 和 7 确认了该 Pod 长期处于 Pending 状态且从未重启。
- **已知盲区**：ConfigMap 缺失的具体原因（创建失败、拼写错误或意外删除）在当前事实中未明确（证据中的 `unknowns` 字段），这不影响“挂载失败”这一直接根因的判定，但属于导致该现象的潜在上游未知因素。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 19.4s
├─ 并发证据采集: 40.9s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 40.9s (Evidence 33.2s, RCA 7.6s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed
