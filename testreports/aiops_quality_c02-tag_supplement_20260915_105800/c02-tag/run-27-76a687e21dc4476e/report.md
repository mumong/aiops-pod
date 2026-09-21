## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod aiops-case-v07/workload 配置使用的容器镜像 registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908 在镜像仓库中不存在（Tag Not Found），导致 kubelet 持续拉取失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status`: Pending, `pod.phase`: Pending | 确认工作负载处于不可用状态 |
| 2 | K8s State | kubernetes | `container.waiting_reason`: ImagePullBackOff (Container: app) | 直接指示镜像拉取失败 |
| 3 | K8s Event | kubernetes | `Error: ErrImagePull` (x4, 31m前) | 记录初始拉取失败事件 |
| 4 | K8s Event | kubernetes | `Failed to pull image ...: rpc error: code = NotFound desc = failed to resolve reference ...: not found` (x4) | 明确镜像仓库返回 404 或 Tag Not Found 错误 |
| 5 | K8s Event | kubernetes | `Back-off pulling image "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` (x132 over 32m) | 证实 kubelet 持续重试并退避 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (label: `reason=ImagePullBackOff`, `value=1`) | 确认当前正在处于拉取退避状态的 Pod |
| 7 | K8s Config | kubernetes | `container.resource_limit.cpu`: 50m, `container.resource_limit.memory`: 32Mi | 排除资源限制导致的拉取失败 |

上述 K8s 状态和事件事实一致显示 Pod 因镜像不存在 (`NotFound`) 而持续处于 `ImagePullBackOff` 状态；Metric 数据证实该状态是当前且持续的；日志/链路不可用因容器未启动，符合预期。

## 🎯 根因分析 · g1

### 因果链

```text
配置引用不存在的容器镜像 (registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908) → kubelet 拉取镜像被镜像仓库拒绝 (NotFound) → 容器无法启动并持续重试退避 → Pod 处于 ImagePullBackOff 和 Pending 状态
```

### 根因结论

已确认的根因是 Pod `aiops-case-v07/workload` 配置的容器镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在镜像仓库中不存在。

该根因直接导致了以下现象：
1. kubelet 在拉取该镜像时收到 `code = NotFound` 错误（证据 #4）。
2. Pod 因无法启动容器而进入 `ImagePullBackOff` 等待状态（证据 #2, #3, #4）。
3. Pod 最终停留在 `Pending` 阶段，无法进入运行状态（证据 #1）。

证据充分，无需补充决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 17.4s
├─ 并发证据采集: 35.5s
│  └─ g1 aiops-case-v07/workload: 35.5s (Evidence 29.9s, RCA 5.5s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
