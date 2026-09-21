## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | aiops-case-v07/workload Pod 处于 ImagePullBackOff 状态，容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Error: ErrImagePull` (fact-24f2099a9f3a), `Error: ImagePullBackOff` (fact-8acc0877515a) | 确立异常状态及重试机制触发 |
| 2 | K8s Event | Kubernetes | `Failed to pull image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908": ... registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908: not found` (fact-cec71393ec10) | 确认底层镜像缺失事实及具体缺失的 registry 路径 |
| 3 | K8s State | Kubernetes | 容器状态：`waiting_reason: ImagePullBackOff` (fact-e1fa26e99ec6), `waiting_message: Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` (fact-54e7bc36e84b) | 明确 K8s 层面的异常原因与当前容器状态 |
| 4 | K8s State | Kubernetes | Pod 状态：`phase: Pending` (fact-07911fefcd69), `ContainersNotReady` (fact-43766f279bed) | 确认 Pod 处于阻塞状态，且未发生 CrashLoopBackOff (restart_count: 0) |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` (fact-2315f38d6282) | 时序数据佐证容器处于 ImagePullBackOff 状态，确认现象 |

**证据综合说明**：
K8s Events (行 1-2) 提供了从拉取失败到进入退避状态的完整序列，其中行 2 的 `not found` 错误直接定位到镜像地址问题。K8s State (行 3-4) 和 Metric (行 5) 分别从实例状态和监控数据上相互印证，排除了应用启动后因 OOM 或错误退出导致的问题，确认为启动前置条件不满足。

## 🎯 根因分析 · g1

### 因果链
```text
manifest 引用的镜像 tag 在 registry 不存在 → kubelet 拉取镜像报 NotFound 错误 → 容器进入 ErrImagePull 并退避 → Pod 处于 Pending/ImagePullBackOff 状态
```

### 根因结论
已确认根因：Pod 定义的镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在目标 Registry 中不存在（返回 `not found`），导致 kubelet 无法拉取基础容器镜像，进而使 Pod 无法进入 Running 状态。

支撑证据：
- **镜像缺失**：K8s Event 明确记录 `Failed to pull image ... not found` (行 2)；
- **状态确认**：K8s 状态显示 `waiting_reason: ImagePullBackOff` (行 3) 且 Metric 显示 `waiting_reason{reason="ImagePullBackOff"} = 1` (行 5)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 13.6s
├─ 并发证据采集: 35.9s
│  └─ g1 aiops-case-v07/workload: 35.8s (Evidence 28.0s, RCA 7.7s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
