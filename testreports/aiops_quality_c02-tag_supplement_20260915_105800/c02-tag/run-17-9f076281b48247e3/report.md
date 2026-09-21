## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | aiops-case-v07/workload 处于 ImagePullBackOff 状态，Pod 无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase = Pending` | 确认 Pod 处于不可用状态 |
| 2 | K8s Event | kubernetes | `Failed to pull image ... rpc error: code = NotFound desc = failed to resolve reference "registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908"` | 直接证实镜像拉取因目标 Tag 不存在而失败 |
| 3 | K8s State | kubernetes | `container.waiting_reason = ImagePullBackOff` | 反映 kubelet 正在指数退避重试拉取失败镜像 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` | 从监控侧证实 Pod 容器正处于镜像拉取失败等待状态 |

**证据关系说明：**
Kubernetes 事件（证据 2）提供了具体的镜像仓库 404 错误细节，直接解释了 K8s 状态（证据 3）中 `ImagePullBackOff` 的成因；Prometheus 指标（证据 4）独立印证了 K8s 中观察到的状态异常。日志与链路追踪因容器未启动而不适用。

## 🎯 根因分析 · g1

### 因果链

```text
镜像 tag 'aiops-fixture-unavailable-20260908' 不存在 → 容器运行时拉取镜像返回 NotFound 错误 → Pod 状态转为 ImagePullBackOff 并停止重试 → 应用服务不可用
```

### 根因结论

已确认根因为：Pod 配置引用的镜像 tag `aiops-fixture-unavailable-20260908` 在指定仓库 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause` 中不存在。
- 故障机制：容器运行时尝试拉取该镜像时收到 `NotFound` 错误（证据 2）。
- 故障表现：Kubelet 进入 `ImagePullBackOff` 等待状态（证据 3），导致 Pod 无法调度为 `Running`，应用不可用（证据 1, 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 15.7s
├─ 并发证据采集: 39.4s
│  └─ g1 aiops-case-v07/workload: 39.4s (Evidence 30.7s, RCA 8.6s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
