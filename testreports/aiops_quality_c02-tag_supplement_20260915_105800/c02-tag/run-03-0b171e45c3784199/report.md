## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | 指定镜像 (registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908) 在镜像仓库中不存在 (manifest unknown/not found)。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Failed ... rpc error: code = NotFound ... failed to resolve reference ... pause:aiops-fixture-unavailable-20260908: not found` | 确认镜像解析失败的具体错误原文，指向镜像不存在 |
| 2 | K8s State | kubernetes | `container.waiting_reason="ImagePullBackOff"` (container=app) | 明确容器的异常状态 |
| 3 | K8s State | kubernetes | `container.waiting_message="Back-off pulling image \"registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908\""` | 指出受影响的镜像名与标签 |
| 4 | K8s State | kubernetes | `pod.status="Pending"` | 确认 Pod 因无法拉起而卡在 Pending 阶段 |
| 5 | K8s Event | kubernetes | `Normal BackOff ... Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` (x7) | 佐证 K8s 在持续重试失败，符合镜像不可达的异常模式 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ImagePullBackOff"} = 1` | 独立于 K8s 状态的指标确认，与 K8s State 一致 |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total{container="app"} = 0` | 确认容器从未启动成功过，排除了启动后崩溃导致重启的可能 |

**证据分析：**
K8s 事件与状态直接给出了根本原因：镜像不存在（not found）。Metric 数据证实了等待原因的准确性，且重启数为 0，完全排除了运行时崩溃的可能性。Logging 和 Tracing 因容器未启动而不存在数据，属于物理现象，与镜像拉取失败的事实不冲突。

## 🎯 根因分析 · g1

### 因果链
```text
镜像仓库中不存在指定镜像 (registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908) → 镜像拉取解析失败 (not found) → kubelet 持续 Back-off 重试拉取 → Pod 状态变为 ImagePullBackOff 且卡在 Pending 状态
```

### 根因结论
已确认的根因是：工作负载配置的容器镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在对应的镜像仓库中不存在（manifest not found）。
- 证据 1 和 3 明确指出拉取该特定镜像版本时返回 `NotFound` 错误。
- 证据 2、4 和 6 确认了该失败导致容器进入 `ImagePullBackOff` 等待状态。
- 证据 5、7 佐证了重试失败和未启动的事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 23.9s
├─ 并发证据采集: 35.7s
│  └─ g1 aiops-case-v07/workload: 35.7s (Evidence 29.3s, RCA 6.2s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
