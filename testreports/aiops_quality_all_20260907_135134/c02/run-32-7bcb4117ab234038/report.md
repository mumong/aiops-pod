## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod spec中配置的镜像仓库域名'registry.invalid'为无效保留域名，导致DNS解析失败无法拉取镜像 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-da7df230458f` | `Error: ErrImagePull` (34m 前发生) | 确认镜像拉取过程在早期即遭遇网络层拒绝 |
| 2 | K8s Event | `fact-e28708b32c10` | `Failed to pull image... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 提供决定性证据：DNS 无法解析目标域名 `registry.invalid` |
| 3 | K8s State | `fact-0abbb172a3a1` | `container.waiting_reason: "ImagePullBackOff"` | 确认 kubelet 已进入重试退避等待状态 |
| 4 | K8s State | `fact-609f9f566c82` | `pod.phase: "Pending"` | 确认 Pod 始终停留在调度后的等待阶段，未进入运行期 |
| 5 | Metric | `fact-9aef0836345e` | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff", container="app"} = 1` | 指标层面的独立观测，证实镜像拉取处于不可恢复的等待状态 |

**证据总结：**
Kubernetes 事件日志（#2）揭示了最底层的故障原因是 DNS 解析失败（`no such host`），该事实直接导致了镜像拉取异常（#1）。当前的容器状态为 `ImagePullBackOff`（#3）且 Pod 处于 `Pending`（#4），配合 Prometheus 指标（#5），共同证实了故障是由无法访问的镜像仓库导致的镜像拉取阻塞。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec配置了无效域名(registry.invalid) → DNS解析失败(no such host) → 镜像拉取失败(ImagePullBackOff) → Pod处于Pending状态
```

### 根因结论

**已确认的根因：** Pod Spec 中配置的容器镜像仓库域名 `registry.invalid` 为无效保留域名。

**分析：** 该域名无法被 DNS 服务器解析（事实 #2），导致 kubelet 在尝试从远程仓库拉取镜像 `registry.invalid/aiops/workload:missing` 时直接遭遇连接失败。这解释了为何容器始终卡在 `Pending` 状态（事实 #4），且不断触发 `ImagePullBackOff` 重试事件（事实 #3, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 22.9s
├─ 并发证据采集: 37.3s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 37.3s (Evidence 32.0s, RCA 5.2s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
