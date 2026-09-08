## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod 配置的镜像仓库域名 registry.invalid 无法通过 DNS 解析，导致 kubelet 拉取镜像时网络请求失败并进入持续 Back-off 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod `workload-65b7f54794-nqrzv` (aiops-case-02) | `Waiting Reason`: `ImagePullBackOff`, `Message`: `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 确认容器应用 `app` 因镜像拉取失败而处于等待状态 |
| 2 | K8s State | Pod `workload-65b7f54794-nqrzv` | `phase`: `Pending`, `Ready`: `False` (reason: `ContainersNotReady`) | 确认 Pod 处于挂起状态，未就绪 |
| 3 | K8s Config | Pod `workload-65b7f54794-nqrzv` | 容器 `app` 限制: `cpu=50m, memory=32Mi`; 请求: `cpu=5m, memory=8Mi` | 提供资源配额上下文，确认非资源限制导致的调度失败 |
| 4 | Metric | Prometheus `kube_pod_container_status_waiting_reason` | `container="app", reason="ImagePullBackOff"`, value: `1` (采样数: 1) | 独立验证了 K8s State 的容器异常状态 |

**证据关联说明：**
Kubernetes 状态直接显示了容器处于 `ImagePullBackOff` 状态并伴有明确的镜像拉取错误信息，Metrics 的 Prometheus 指标与该状态精确对应。由于容器从未成功启动，日志（Logging）和追踪（Tracing）维度为空，K8s 状态与 Metric 共同构成了完整的诊断证据链。

## 🎯 根因分析 · g1

### 因果链

```text
镜像仓库域名 registry.invalid DNS 解析失败 → Kubelet 拉取镜像网络请求报错 → 容器进入 Back-off 拉取重试状态 → Pod 持续 Pending 且容器不就绪
```

### 根因结论

已确认的根因为 **镜像仓库域名 `registry.invalid` 无法通过 DNS 解析**。

该原因直接导致了 `ImagePullBackOff` 异常，并引发了 `Pod Pending` 的现象。证据链由 K8s `waiting_message`（包含具体错误域名）、`waiting_reason`（`ImagePullBackOff`）以及 Prometheus 对应指标 `container_status_waiting_reason` 互相印证。因容器未启动，不存在运行时相关的日志或追踪数据，现有证据足以闭合该异常组的诊断逻辑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 17.5s
├─ 并发证据采集: 35.6s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 35.6s (Evidence 31.2s, RCA 4.2s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
