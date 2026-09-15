## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod 配置中使用了无效的镜像仓库域名 'registry.invalid'，该域名属于 RFC 6761 保留域名，无法通过 DNS 解析，导致容器镜像拉取持续失败并进入 ImagePullBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Failed to pull image "registry.invalid/aiops/workload:missing": rpc error... Head "https://registry.invalid/v2/...": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-0bbf45e0ca6b) | 确认镜像拉取失败的直接原因是无法解析 DNS 域名 `registry.invalid` |
| 2 | K8s State | Kubernetes | `container.waiting_reason: "ImagePullBackOff"` (fact-6d5771aa79b8) | 描述 Pod 最终异常状态 |
| 3 | K8s Config | Kubernetes | `container.resource_request.memory: "8Mi"` (fact-4aa01fea8460) | 资源请求值极小，但非导致镜像拉取失败的原因 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值 `1` (reason="ImagePullBackOff") (fact-41f425062eb5) | 确认容器状态为镜像拉取失败 |

**证据说明：**
Kubernetes 事件与 Prometheus 指标均确认了 `ImagePullBackOff` 的异常状态。Kubernetes 事件提供了决定性的诊断信息，明确指出失败原因为 DNS 解析 `registry.invalid` 失败，排除了网络或存储等其他潜在因素。

## 🎯 根因分析 · g1

### 因果链

```text
使用了无效的镜像仓库域名 'registry.invalid' → DNS 解析失败 (no such host) → 镜像拉取失败 (ImagePullBackOff) → Pod 进入 Pending 状态且不可用
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-02/workload-65b7f54794-z7kdp` 的容器配置中使用了无效的镜像仓库域名 `registry.invalid`。该域名无法通过 DNS 解析，导致容器镜像拉取持续失败，最终使容器进入 `ImagePullBackOff` 状态（证据 1、2、4）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 34.0s
├─ 并发证据采集: 86.6s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 86.6s (Evidence 80.6s, RCA 5.9s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
