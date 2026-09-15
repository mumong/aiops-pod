## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | aiops-case-v07/workload Pod 持续处于 ImagePullBackOff 状态，未能启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `phase: Pending`, `condition: ContainersReady=False (ContainersNotReady)` | 确证 Pod 处于不可用且未就绪的状态 |
| 2 | K8s Event | Kubernetes | `message: Failed to pull image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908": rpc error: code = NotFound` | 提供镜像拉取失败的直接原因，确证远程仓库不存在该 tag |
| 3 | K8s State | Kubernetes | `container.waiting_reason: ImagePullBackOff`, `message: Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` | 确证 kubelet 已进入指数退避重试机制 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1 (labels: reason=ImagePullBackOff)`, `kube_pod_container_status_restarts_total=0` | 独立验证容器处于 Waiting 状态，且无重启历史，符合拉取失败特征 |

**证据说明：**
Kubernetes 事件与容器状态互相印证，均指向同一镜像拉取失败且触发 BackOff。Metric 独立确认了这一结果状态，排除了短暂波动。由于容器未启动，Logging/Tracing 缺失属物理限制，不影响基于 K8s 状态的判定。

## 🎯 根因分析 · g1

### 因果链

```text
已验证的 Pod Spec 引用不存在的镜像 tag → kubelet 拉取镜像时被仓库返回 NotFound 错误 → ImagePull 失败触发指数退避重试 (BackOff) → 容器状态保持 Waiting/ImagePullBackOff，Pod 处于 Pending
```

### 根因结论

**已确认的根因：** 异常由 Pod 配置中引用的镜像 Tag `aiops-fixture-unavailable-20260908` 在远程仓库中不存在（NotFound）导致（证据：事件 `fact-b225763a6865` 与容器状态 `fact-661697ebaaff`）。该错误直接阻止了容器启动，进而引发 Kubelet 的 BackOff 重试机制，表现为集群中 `aiops-case-v07/workload` 持续处于 `ImagePullBackOff` 状态（证据：`fact-a0eeebad0559`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 19.9s
├─ 并发证据采集: 42.6s
│  └─ g1 aiops-case-v07/workload: 42.6s (Evidence 32.5s, RCA 9.9s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
