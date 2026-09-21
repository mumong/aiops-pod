## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v07/workload` | ImagePullBackOff | Pod aiops-case-v07/workload 处于 ImagePullBackOff 状态，处于 Pending 阶段且未启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason: ImagePullBackOff` (Container: app) | 确认容器处于拉取失败的退避状态 |
| 2 | K8s State | Kubernetes | `container.waiting_message: "Back-off pulling image \"registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908\""` | 指出引发拉取失败的具体镜像及 Registry |
| 3 | K8s State | Kubernetes | `pod.phase: Pending`, `condition.Ready: False` (ContainersNotReady), `restart_count: 0` | 确认 Pod 始终处于初始化阶段，且未产生任何重启事件 |
| 4 | K8s Config | Kubernetes | `resource_request.cpu: 5m`, `resource_limit.memory: 32Mi` | 排除资源配额导致的调度或运行异常 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason: 1` (Reason: ImagePullBackOff) | 独立于 Kubernetes API 确认容器等待状态的客观指标 |
| 6 | Metric | Prometheus | `kube_pod_status_phase: 1` (Phase: Pending), `kube_pod_container_status_restarts_total: 0` | 验证 Pod 长期滞留且无重启行为，佐证非应用侧崩溃 |

**证据关联说明：**
Kubernetes 状态与 Prometheus 指标完全一致，均指向 `ImagePullBackOff` 和 `Pending`。由于 `restart_count` 为 0 且 Kubelet 持续重试，说明问题发生在镜像拉取阶段（镜像不可用），而非容器启动后的应用崩溃或资源竞争。

## 🎯 根因分析 · g1

### 因果链

```text
Registry 返回镜像 tag 不存在 (NotFound) → 容器运行时无法拉取并解压镜像 → Kubelet 持续重试失败并进入 Back-off → Pod 状态维持 ImagePullBackOff
```

### 根因结论

已确认的根因是：Pod 引用的容器镜像 `registry.cn-hangzhou.aliyuncs.com/google_containers/pause:aiops-fixture-unavailable-20260908` 在指定 Registry 中不存在（NotFound）。这导致容器运行时无法获取镜像层，Kubelet 因持续拉取失败而进入指数退避（Back-off）等待，从而使 Pod 持续处于 `Pending` 阶段且无法进入 `Running` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 19.5s
├─ 并发证据采集: 45.5s
│  └─ g1 aiops-case-v07/workload: 45.5s (Evidence 37.4s, RCA 8.0s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v07/workload**: pod-imagepull-failed
