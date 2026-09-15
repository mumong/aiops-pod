## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod aiops-case-v07/workload 配置的镜像 'registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908' 在指定的远程仓库中不存在（NotFound），导致 Kubelet 无法拉取镜像，引发持续重试与 ImagePullBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `rpc error: code = NotFound desc = ... registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908: not found` (fact-ae9f83aa5584) | 确认镜像在远端仓库不存在，为根本原因 |
| 2 | K8s Event | kubernetes | `Warning Failed ... Error: ImagePullBackOff` (fact-a571c202e26d) | 确认 Kubelet 拉取失败并进入退避等待状态 |
| 3 | K8s Event | kubernetes | `Normal BackOff ... Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` (fact-3c751706b176) | 确认 Kubelet 正在持续重试拉取该特定镜像 |
| 4 | K8s State | kubernetes | `status: Pending` (fact-2263f21119b1) | 确认 Pod 处于挂起状态，无法调度到 Running |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1`, `reason="ImagePullBackOff"` (fact-e86895babb41) | 从监控数据确认当前容器处于镜像拉取回退状态 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total=0` (fact-aab1a42d9be5) | 证明容器从未启动过，排除了启动后崩溃（CrashLoopBackOff）的可能性 |

**证据关联说明：**
证据 1 和 2 建立了从“远端仓库镜像缺失”到“Kubelet 报错”的直接因果链条；证据 3 佐证了该报错的持续性（持续 46 分钟）；证据 4 和 5 分别从 Pod 生命周期状态和指标层面确认了最终现象；证据 6 排除了应用逻辑导致的崩溃，锁定在镜像拉取阶段。

## 🎯 根因分析 · g1

### 因果链

```text
远端镜像仓库不存在指定版本 -> Kubelet 拉取镜像失败(NotFound) -> Kubelet 进入 BackOff 状态 -> Pod 持续处于 Pending/ImagePullBackOff
```

### 根因结论

已确认的根因为：Pod `aiops-case-v07/workload` 配置的镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在指定的远程仓库中不存在（NotFound）。
此事实直接导致 Kubelet 无法拉取镜像，进而引发 `ImagePullBackOff` 状态和 Pod 挂起。证据链完整：
- **原因端**：远程仓库返回 `NotFound` (fact-1)
- **机制端**：Kubelet 报错 `Failed to pull` 并进入 `BackOff` (fact-2, fact-3)
- **现象端**：Pod 状态为 `Pending` (fact-4)，指标显示 `waiting_reason=ImagePullBackOff` (fact-5) 且 `restarts=0` (fact-6)

现有证据足以确诊根因，无需补充其他决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 19.5s
├─ 并发证据采集: 29.8s
│  └─ g1 aiops-case-v07/workload: 29.8s (Evidence 23.2s, RCA 6.5s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
