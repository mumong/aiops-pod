## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | DNS解析失败导致无法拉取镜像：Kubelet在尝试从无效仓库域名 registry.invalid 拉取镜像时，因DNS服务器（127.0.0.53）无法解析该主机名，导致连接失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | K8s `event.message` | `Failed to pull image "registry.invalid/aiops/workload:missing": ... failed to resolve reference ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 直接证实 DNS 解析失败，明确指向无效域名 `registry.invalid` 和 DNS 服务器 `127.0.0.53` 报错。 |
| 2 | K8s Event | K8s `event.message` | `Error: ImagePullBackOff` / `Back-off pulling image "registry.invalid/aiops/workload:missing"` | 证实拉取失败后的重试与退避机制，确认故障持续存在。 |
| 3 | K8s State | K8s `pod.status` | `Pending` | 证实 Pod 因镜像无法拉取而卡止在 Pending 状态。 |
| 4 | Metric | Prometheus `kube_pod_container_status_waiting_reason` | 1 (labels: `reason=ImagePullBackOff`) | 观测确认容器处于等待原因 `ImagePullBackOff` 状态。 |

**证据印证说明**：K8s Event 中的 `no such host` 具体报错证实了 `registry.invalid` 域名的不可达性；Metrics 观测到的 `ImagePullBackOff` 状态与 K8s Event 中的重试记录完全吻合；状态为 `Pending` 证实了故障直接导致 Pod 无法正常启动，而非运行崩溃。Logging 和 Tracing 因容器未启动而物理上缺失，符合预期。

## 🎯 根因分析 · g1

### 因果链

```text
镜像仓库域名无效或DNS配置缺失 (registry.invalid) → DNS解析失败 (no such host) → 镜像拉取失败 (ImagePullBackOff) → Pod 处于 Pending 状态
```

### 根因结论

已确认根因为**镜像仓库域名配置无效导致 DNS 解析失败**。

1.  **机制确认**：Kubelet 尝试拉取镜像 `registry.invalid/aiops/workload:missing` 时，DNS 服务器 (`127.0.0.53`) 无法解析该主机名（`fact-8d9cf6136e16`），导致连接建立失败。
2.  **状态确认**：拉取失败触发了容器的 `ImagePullBackOff` 状态，致使 Pod 一直停留在 `Pending` 状态（`fact-57e2afa89369`、`fact-2514836ff2be`）。
3.  **结论**：集群问题的根本原因在于容器配置中引用的镜像仓库地址 `registry.invalid` 在集群网络中无法通过 DNS 解析，导致镜像拉取流程中断。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 22.3s
├─ 并发证据采集: 76.4s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 76.4s (Evidence 70.2s, RCA 6.1s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
