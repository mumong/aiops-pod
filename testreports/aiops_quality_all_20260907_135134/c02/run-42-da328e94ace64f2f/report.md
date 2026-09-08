## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-nqrzv 处于 ImagePullBackOff 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-e856e78767e7) | 直接记录 kubelet 拉取失败原因，确认为 DNS 解析失败 |
| 2 | K8s State | Kubernetes | `status: Pending` (fact-d2f6cb74a608) | 证实 Pod 因镜像拉取失败无法进入运行状态 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (ImagePullBackOff) (fact-1253ba59e102) | 指标确认容器处于等待拉取镜像的状态 |

证据表明 Pod 因无法解析 `registry.invalid` 导致镜像拉取持续失败，且无容器运行，故 Metric 和 K8s 状态一致反映此网络/配置错误。

## 🎯 根因分析 · g1

### 因果链

```text
镜像域名 registry.invalid DNS 解析失败 (lookup no such host) → kubelet 无法连接镜像仓库 (dial tcp error) → 镜像拉取失败 (ErrImagePull) → Pod 状态为 ImagePullBackOff/Pending
```

### 根因结论

已确认根因：镜像仓库域名 `registry.invalid` 解析失败（DNS resolution failure），导致 kubelet 无法获取镜像 manifest。此结论直接由 K8s Event 中的 `dial tcp: lookup registry.invalid ... no such host` 错误支撑，且 Metric 确认了该 Pod 处于 `ImagePullBackOff` 等待状态。

---

## 📊 性能统计

```text
├─ 总耗时: 56.9s
├─ 问题定位: 15.6s
├─ 并发证据采集: 35.0s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 35.0s (Evidence 25.3s, RCA 9.6s)
└─ 汇总总结: 6.3s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
