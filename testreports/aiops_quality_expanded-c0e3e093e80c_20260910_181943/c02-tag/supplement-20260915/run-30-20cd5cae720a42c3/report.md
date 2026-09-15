## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | 镜像引用配置错误：容器映像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在仓库中不存在（返回 NotFound/manifest unknown），导致 kubelet 无法拉取 pause 辅助容器，Pod 持续处于 ImagePullBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `rpc error: code = NotFound desc = failed to pull ... pause:aiops-fixture-unavailable-20260908 ... not found` | 直接证明镜像注册表返回 404，确认为镜像引用配置错误 |
| 2 | K8s Event | kubernetes | `Normal BackOff pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` | 展示 kubelet 持续拉取失败并进入退避循环的状态 |
| 3 | K8s State | kubernetes | `pod.status: Pending` | 描述 Pod 的当前生命周期状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (labels: `reason="ImagePullBackOff"`) | 独立确认等待原因为镜像拉取失败 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total=0` (labels: `container="app"`) | 排除应用逻辑导致容器重启的可能性 |

**证据分析：**
- **K8s Event** 提供了最直接的证据：注册表明确返回 `code = NotFound`，结合 `BackOff` 事件表明这是一个持续存在的配置错误而非临时网络抖动。
- **Metric** 中的 `ImagePullBackOff` 状态与 **K8s Event** 中的 `BackOff` 现象完全印证。
- **Metric** 显示重启次数为 0，排除了应用侧异常崩溃，确认问题发生在启动前的镜像拉取阶段。

## 🎯 根因分析 · g1

### 因果链

```text
镜像 Tag 错误/不存在 (registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908) → Registry 返回 NotFound 错误 → Kubelet 持续重试拉取并触发指数退避 (Back-off pulling image) → Pod 状态 Pending，容器 Waiting (ImagePullBackOff)
```

### 根因结论

**已确认的根因：镜像引用配置错误。**

容器映像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在仓库中不存在（返回 NotFound/manifest unknown）。这导致 kubelet 无法拉取 pause 辅助容器，引发容器持续处于 `ImagePullBackOff` 状态 [1, 2]。**Metric** 数据确认了 `ImagePullBackOff` 的等待原因且重启计数为 0，进一步排除了其他启动故障 [4, 5]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 24.2s
├─ 并发证据采集: 39.9s
│  └─ g1 aiops-case-v07/workload: 39.9s (Evidence 31.2s, RCA 8.6s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
