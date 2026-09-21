## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | aiops-case-v07/workload Pod 处于 ImagePullBackOff 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: "ImagePullBackOff" (app) | 确认容器当前处于拉取失败的重试等待阶段 |
| 2 | K8s State | kubernetes | `container.waiting_message`: "Back-off pulling image \"registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908\"" | 提供镜像拉取失败的具体详情和退避状态 |
| 3 | K8s Event | kubernetes | "Failed to pull image ...: rpc error: code = NotFound desc = ... not found" | 根本证据：Registry 明确返回 404，证实镜像 tag 不存在 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (container=app, reason=ImagePullBackOff): 1 | 提供集群侧关于该容器等待原因的独立验证 |
| 5 | K8s Config | kubernetes | `container.resource_request.cpu`: "5m" (app) | 排除因资源请求不足导致 Pod 调度过慢或处于 Pending 状态的可能 |

**证据说明：**
- 证据 1 与 3 相互印证：K8s Event 中的 `code = NotFound` 直接解释了 K8s State 中 `waiting_reason` 变为 `ImagePullBackOff` 的物理原因（无法获取镜像即停止重试并进入 Back-off）。
- 证据 4 的 Prometheus Metric 数据与证据 1 的 K8s 状态一致，排除了单一视图采集异常或状态未同步的可能。
- 证据 5 证实 Pod 未因资源不足被调度器搁置（当前处于 Pending 是因为容器未就绪而非未调度）。

## 🎯 根因分析 · g1

### 因果链

```text
指定镜像 tag (pause:aiops-fixture-unavailable-20260908) 在仓库中不存在 → Kubelet 尝试拉取镜像遭遇 NotFound 错误 → 容器持续进入 ImagePullBackOff 状态 → Pod 保持 Pending 状态，应用不可用
```

### 根因结论

已确认根因：**Pod 指定的容器镜像在远程仓库中不存在（Tag 错误或镜像已移除），导致镜像拉取失败，进而引发 Pod 无法进入 Running 状态。**

- 证据 3 (K8s Event) 明确指出 `rpc error: code = NotFound`，表明 Kubelet 向 registry 查询时，目标 image tag `aiops-fixture-unavailable-20260908` 无法找到。
- 证据 2 (K8s State) 和 证据 4 (Metric) 一致确认容器当前正在因拉取失败而进行指数退避（Back-off pulling image）。
- 由于容器始终无法成功拉取镜像，Pod 的 `Ready` 条件无法满足（证据 1），整个应用服务因此不可用。

---

## 📊 性能统计

```text
├─ 总耗时: 59.6s
├─ 问题定位: 12.7s
├─ 并发证据采集: 36.8s
│  └─ g1 aiops-case-v07/workload: 36.8s (Evidence 28.6s, RCA 8.0s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
