## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod 配置的镜像 tag 'aiops-fixture-unavailable-20260908' 在指定远程仓库中不存在 (404 Not Found)，导致 kubelet 无法拉取镜像并持续进入 ImagePullBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: app 容器为 `ImagePullBackOff` | 确认 Pod 当前处于因镜像拉取失败而等待的状态 |
| 2 | K8s Event | Kubernetes | `Failed`: `Error: ErrImagePull` (14m, x6 over 16m) | 确认 Pod 持续发生镜像拉取错误 |
| 3 | K8s Event | Kubernetes | `Failed`: `failed to resolve reference "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908": not found` (14m) | 提供决定性的故障根因：指定镜像标签在仓库中不存在 (404) |
| 4 | K8s Event | Kubernetes | `BackOff`: `Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` (58s, x66 over 16m) | 证实 kubelet 已因连续拉取失败进入指数退避重试机制 |
| 5 | K8s State | Kubernetes | `pod.status`: `Pending`, `ContainersNotReady` | 确认 Pod 因镜像未就绪而停留在 Pending 阶段 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (labels: `container=app`, `reason=ImagePullBackOff`) | 独立观测指标确认 app 容器持续处于 ImagePullBackOff 状态 |

**证据关联说明：**
Kubernetes Event #3 直接指出了镜像 `aiops-fixture-unavailable-20260908` 在远程仓库 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause` 中缺失 (not found)，解释了 Event #2 中的 ErrImagePull 原因，并导致了 Event #4 中的 BackOff 行为。Metric #6 与 K8s State #1 从监控指标层面独立印证了该异常状态的持续性。

## 🎯 根因分析 · g1

### 因果链

```text
远程镜像仓库不存在指定的镜像 tag (404 Not Found) → kubelet 拉取镜像失败触发 ErrImagePull → 连续重试失败并进入指数退避 (BackOff) → Pod 主容器持续处于 ImagePullBackOff 状态，Pod 停留在 Pending 阶段
```

### 根因结论

**已确认的根因：**
Pod 配置中引用的镜像标签 `aiops-fixture-unavailable-20260908` 在远程仓库 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause` 中不存在。

**证据支撑：**
- 该结论由 Kubernetes Event (fact-d09a57d1bd62) 提供的 `not found` 错误原文直接证实，表明 404 响应是拉取失败的初始原因。
- 后续的 `ImagePullBackOff` 状态 (fact-29e8bc3b2b17, fact-24adee4fedac) 是该镜像无法拉取导致的直接结果和系统响应。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 29.3s
├─ 并发证据采集: 30.8s
│  └─ g1 aiops-case-v07/workload: 30.8s (Evidence 22.3s, RCA 8.3s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
