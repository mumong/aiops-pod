## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | 镜像 tag 'aiops-fixture-unavailable-20260908' 在镜像仓库中不存在 (NotFound) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.aiops-case-v07/workload | `Pending` 阶段；`ContainersReady=False`；`restart_count=0` | 确认 Pod 处于初始等待状态，未启动且未发生重启 |
| 2 | K8s State | container.app | `waiting_reason=ImagePullBackOff`，`waiting_message=Back-off pulling image "..."` | 直接指出容器处于镜像拉取退避状态 |
| 3 | K8s Event | kubelet | `Failed to pull image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908": ... not found` (fact-9cb8e794f87b) | 确认镜像拉取失败的直接原因为 `NotFound`，镜像 tag 不存在 |
| 4 | K8s Event | kubelet | `Error: ImagePullBackOff` (fact-15aa25cc97ac)，`Back-off pulling image` (fact-4e5604cc852d) | 持续观察到拉取失败引发的退避行为，印证了镜像不可用的事实 |
| 5 | Metric | kube_pod_container_status_waiting_reason | `ImagePullBackOff` 计数为 1 (fact-392e57e27f94) | 独立确认了容器的 `ImagePullBackOff` 状态，与 K8s 事件互相印证 |
| 6 | Metric | kube_pod_container_status_restarts_total | `restart_count` 为 0 (fact-8afbeeff4a09) | 证明容器尚未成功启动过，排除因启动崩溃导致的现象 |

**证据小结**
K8s 状态、事件流与 Prometheus 指标在现象维度高度一致：Pod 持续处于 `Pending` 且未重启，容器处于 `ImagePullBackOff` 状态。事件日志明确提供了 `NotFound` 的错误根因，证明容器启动受阻并非由于资源不足或网络问题，而是镜像本身在仓库中不存在。

## 🎯 根因分析 · g1

```text
镜像 tag 'aiops-fixture-unavailable-20260908' 在镜像仓库中不存在 (NotFound) → 镜像拉取请求被注册拒绝并返回 NotFound → kubelet 进入 Back-off 退避拉取状态 → Pod 持续处于 Pending 阶段且容器不可用
```

**根因结论**
已确认根因：
**镜像 tag `aiops-fixture-unavailable-20260908` 在镜像仓库中不存在 (NotFound)**，导致 `aiops-case-v07/workload` 中的 `app` 容器无法正常拉取镜像，进而触发 kubelet 的 `Back-off` 机制，使 Pod 长期停留在 `Pending` 状态。此结论由事件记录中的 `NotFound` 错误码及 K8s 状态指标直接证实（见证据表 #3, #2, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 17.2s
├─ 并发证据采集: 33.6s
│  └─ g1 aiops-case-v07/workload: 33.5s (Evidence 28.6s, RCA 4.8s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
