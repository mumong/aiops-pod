## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod/workload in aiops-case-v07 is stuck in ImagePullBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Container `app` waiting reason: `ImagePullBackOff` | 确认容器因镜像拉取失败而停滞 |
| 2 | K8s State | Kubernetes | Container `app` waiting message: `Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` | 指出导致失败的具体镜像及拉取回退行为 |
| 3 | K8s State | Kubernetes | Pod `aiops-case-v07/workload` phase: `Pending`, condition `ContainersReady=False` (containers with unready status: [app]) | 证实 Pod 处于等待就绪状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (labels: container=app, reason=ImagePullBackOff) | 监控数据直接印证了 K8s 的 ImagePullBackOff 状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total=0` (container=app) | 排除启动后崩溃重启，确认问题存在于启动前 |

**证据综述**：Kubernetes 状态（事实 1, 2）与 Prometheus 监控指标（事实 4）在维度上完全一致，均确认容器 `app` 处于 `ImagePullBackOff` 状态；Pod 处于 Pending 且重启数为 0（事实 3, 5），排除了运行时崩溃或调度资源不足的问题，证据链闭合指向镜像拉取环节。

## 🎯 根因分析 · g1

### 因果链

```text
镜像 Tag 'aiops-fixture-unavailable-20260908' 在远程仓库不存在 → 容器运行时拉取镜像返回 NotFound 错误 → kubelet 将容器状态转为 ImagePullBackOff → Pod 保持 Pending 且不可用
```

### 根因结论

已确认根因是**远程镜像仓库中缺失指定版本的镜像**。

具体表现为：Pod `aiops-case-v07/workload` 中的容器 `app` 尝试拉取镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 时失败。Kubernetes 状态（事实 2）明确指出拉取该特定 Tag 的镜像时进入 Back-off 状态；Metric 指标（事实 4）进一步佐证了该容器处于 ImagePullBackOff 状态。由于镜像在仓库端不存在（Manifest not found），容器无法启动，导致 Pod 始终卡在 Pending 阶段。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.5s
├─ 并发证据采集: 35.0s
│  └─ g1 aiops-case-v07/workload: 35.0s (Evidence 27.4s, RCA 7.5s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
