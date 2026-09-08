## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | DNS配置错误导致容器运行时无法解析镜像仓库地址 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Error: ImagePullBackOff`, `Failed to pull image "registry.invalid/aiops/workload:missing": failed to resolve reference... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 证实镜像拉取失败的具体机制是 DNS 解析 `registry.invalid` 失败 |
| 2 | K8s State | Pod | `status: Pending`, `reason: ImagePullBackOff` | 确认 Pod 处于未运行状态，且容器因拉取镜像失败而等待 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = `1` (reason=`ImagePullBackOff`), `kube_pod_container_status_restarts_total` = `0` | 从指标侧印证容器持续处于等待拉取镜像状态，且未发生过重启 |

证据间高度一致：Kubernetes 事件直接捕获了底层 `dial tcp` 失败并归因于 `no such host`，Pod 状态和 Prometheus 指标均在同一时间窗口内反映了容器因镜像拉取失败而处于等待状态，共同指向镜像仓库地址存在解析问题。

## 🎯 根因分析 · g1

### 因果链

```text
镜像仓库地址 (registry.invalid) DNS 解析失败 → 容器运行时无法拉取镜像 → Pod 处于 Pending/ImagePullBackOff 状态
```

### 根因结论

已确认的根因是集群的 DNS 解析配置存在问题（或镜像仓库地址本身未配置有效的 DNS 记录），导致 `registry.invalid` 无法被解析，进而造成容器无法拉取镜像而陷入 `ImagePullBackOff` 状态。

该结论由 Kubernetes 事件中的 `no such host` 错误信息以及 `ImagePullBackOff` 状态直接支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 53.0s
├─ 问题定位: 16.4s
├─ 并发证据采集: 30.0s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 30.0s (Evidence 25.6s, RCA 4.3s)
└─ 汇总总结: 6.6s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
