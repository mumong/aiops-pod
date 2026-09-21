## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod aiops-case-v07/workload 引用的镜像 tag (aiops-fixture-unavailable-20260908) 在远程仓库 registry.cn-hangzhou.aliyuncs.com/google_containers/pause 中不存在 (manifest not found)，导致 kubelet 拉取失败并进入 ImagePullBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-v07/workload` 状态 `Pending`，容器 `app` 状态 `ImagePullBackOff`，原因 `ContainersNotReady` | 确定当前系统处于拉取镜像失败后的退避状态，且未发生重启 |
| 2 | K8s State | Kubernetes | 容器 `app` 请求 `5m CPU` / `8Mi Memory`，限制 `50m CPU` / `32Mi Memory` | 提供资源配置背景，排除资源过载导致的拉取失败 |
| 3 | K8s Event | Kubernetes | `Failed` 错误 `Failed to pull image ".../pause:aiops-fixture-unavailable-20260908": registry... not found` | 记录首次镜像拉取时的明确拒绝原因，确认目标镜像在仓库中不存在 |
| 4 | K8s Event | Kubernetes | `BackOff` 警告 `Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` | 证实 kubelet 因连续失败已进入退避机制，且持续重试失败 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 持续记录容器处于 `ImagePullBackOff` 原因，值为 `1` | 时序数据独立佐证当前拉取失败的持续状态 |

**证据印证：**
Kubernetes 事件（Fact 3, Fact 4）直接暴露了镜像仓库返回的 `not found` 错误及后续的 Back-off 行为，与 K8s 状态（Fact 1, Fact 5）中观察到的 `ImagePullBackOff` 状态高度一致，完整闭环了“请求拉取镜像 -> 仓库拒绝 -> 状态机进入退避”的证据链。

## 🎯 根因分析 · g1

### 因果链

```text
镜像 tag 'aiops-fixture-unavailable-20260908' 在仓库中不存在 (manifest not found) → kubelet 尝试拉取时收到 'NotFound' 错误 → 镜像拉取失败且进入 Back-off 退避阶段 → Pod 状态持续为 Pending (ImagePullBackOff)
```

### 根因结论

已确认根因为：容器镜像标签 `aiops-fixture-unavailable-20260908` 在远程仓库 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause` 中不存在。

该根因由以下事实充分支持：
- **K8s 事件 Fact 3** 显示拉取请求被仓库直接拒绝，报错代码 `NotFound`（manifest not found）。
- **K8s 事件 Fact 4** 显示 kubelet 因此进入 `Back-off` 状态，不再持续高频重试，而是按退避策略重试。
- **K8s 状态 Fact 1** 与 **Metric Fact 5** 共同证实容器卡在这个拉取失败的状态中，且重启次数为 0（Fact 2, Fact 5），表明容器并未尝试运行，排除了运行时错误导致重启的可能。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.7s
├─ 并发证据采集: 39.2s
│  └─ g1 aiops-case-v07/workload: 39.2s (Evidence 29.8s, RCA 9.2s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
