## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | 镜像仓库域名 registry.invalid 配置无效导致 DNS 解析失败，使容器运行时无法拉取镜像。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Failed to pull image "registry.invalid/aiops/workload:missing": ... failed to resolve reference ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 确认拉取失败的直接原因是 DNS 解析 `registry.invalid` 失败 |
| 2 | K8s State | Pod Status | `status: Pending` | 确认 Pod 始终处于等待拉取镜像的阻塞状态 |
| 3 | K8s Event | kubelet | `BackOff pulling image "registry.invalid/aiops/workload:missing"` (发生 155 次，持续 36 分钟) | 证实重试行为持续且失败结果未改变 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (container=app, reason=ImagePullBackOff, value=1) | 从监控指标角度独立确认了镜像拉取阻塞状态 |

**证据说明：**
Kubernetes 事件（#1）明确指出了网络层面的解析失败，配合 `Pending` 状态（#2）和重试事件（#3），形成了从配置错误到容器运行时的完整证据链。Prometheus 指标（#4）从监控维度独立确认了当前容器确实处于 `ImagePullBackOff` 状态，与 K8s 事件描述的故障阶段一致。

## 🎯 根因分析 · g1

### 因果链

```text
无效镜像仓库域名配置 (registry.invalid) → DNS 解析失败 (no such host) → 容器镜像拉取失败 → Pod 处于 Pending/ImagePullBackOff 状态
```

### 根因结论

已确认的根因是 Pod 配置了无效的镜像仓库域名 `registry.invalid`。该域名无法解析导致容器运行时无法获取镜像，直接表现为 Pod 长期停留在 `Pending` 状态且不断重试拉取。此结论得到了 K8s Event 中明确的 DNS 错误原文以及 Prometheus 指标状态的交叉印证。

---

## 📊 性能统计

```text
├─ 总耗时: 52.7s
├─ 问题定位: 18.1s
├─ 并发证据采集: 27.5s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 27.5s (Evidence 22.9s, RCA 4.5s)
└─ 汇总总结: 7.0s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
