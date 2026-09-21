## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod aiops-case-v07/workload 被调度到 node2，但因 Kubelet 在拉取容器镜像 'registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908' 时返回 rpc error: code = NotFound，导致镜像拉取彻底失败，Pod 状态由 ErrImagePull 转为 ImagePullBackOff 并维持在 Pending 阶段。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Failed to pull image ... rpc error: code = NotFound ... not found` (fact-663e974884eb) | 明确镜像拉取失败的底层原因：目标镜像不存在 |
| 2 | K8s Event | kubernetes | `Back-off pulling image ...` (fact-658750019d65) | 确认 Pod 已进入镜像拉取退避重试状态 |
| 3 | K8s State | kubernetes | `container.waiting_reason: "ImagePullBackOff"` (fact-4d5c263ffc6d) | 确认当前容器的确切等待状态 |
| 4 | K8s State | kubernetes | `pod.status: "Pending"` (fact-c08eafc4ac0b) | 确认 Pod 因无法启动容器而停留在 Pending 阶段 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` (fact-812dd40c238d) | 通过监控系统独立验证了当前的 ImagePullBackOff 状态 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total = 0` (fact-97e10a3ef3fc) | 排除因应用崩溃重启（CrashLoopBackOff）导致的现象 |

**证据关联与印证：**
Kubernetes 事件（#1, #2）直接指出镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 因 `NotFound` 而无法拉取，这直接导致了容器状态变为 `ImagePullBackOff`（#3）并使得 Pod 维持在 `Pending` 阶段（#4）。Metric 监控（#5）确认了这一状态在集群层面的持续存在，而重启计数的零值（#6）排除了运行后崩溃的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
目标容器镜像不存在于注册表（NotFound） → Kubelet 拉取失败并进入退避重试 → Pod 状态转为 ImagePullBackOff → 用户可见 Pod 持续处于 Pending 阶段
```

### 根因结论

已确认根因为 **容器镜像拉取失败**。

Pod `aiops-case-v07/workload` 试图拉取名为 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 的镜像，但在请求时注册表返回了 `rpc error: code = NotFound` 错误。由于镜像本身不存在，拉取操作彻底失败。Kubelet 在经历多次失败后进入了退避（Back-off）模式，导致容器无法启动，Pod 长期停留在 `Pending` 状态并表现为 `ImagePullBackOff` 状态。所有相关事实（Kubernetes 事件、状态、Prometheus 指标）均指向且仅支持这一结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 13.4s
├─ 并发证据采集: 54.7s
│  └─ g1 aiops-case-v07/workload: 54.7s (Evidence 47.9s, RCA 6.6s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
