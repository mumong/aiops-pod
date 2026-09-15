## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod配置了无效的镜像仓库域名 registry.invalid，集群DNS无法解析该域名导致镜像拉取失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `phase: Pending` | 确认 Pod 处于待调度完成后的停滞状态 |
| 2 | K8s State | kubernetes | `container.waiting_reason: ImagePullBackOff` (container: app) | 直接定义容器无法进入就绪状态的原因 |
| 3 | K8s Event | kubernetes | `Error: ErrImagePull` 及 `Warning Failed ... Failed to pull image "registry.invalid/aiops/workload:missing"` | 描述拉取失败的第一层异常状态 |
| 4 | K8s Event | kubernetes | `failed to resolve reference "...": failed to do request: Head "https://registry.invalid/v2/...": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 提供根本原因：DNS 解析失败，集群无法定位 registry.invalid 域名 |
| 5 | K8s Event | kubernetes | `BackOff ... Back-off pulling image "registry.invalid/aiops/workload:missing"` | 描述集群在多次重试失败后的退避行为 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason: ImagePullBackOff), `kube_pod_status_phase` = 1 (Pending), `kube_pod_container_status_restarts_total` = 0 | 从指标侧独立印证 Pod 停滞在 Pending 且处于 ImagePullBackOff 状态 |

**证据综合说明：**
Kubernetes 的 State 和 Event 共同锁定异常为镜像拉取阶段，其中 Event 明确指出了 `no such host` 错误，揭示了 DNS 解析失败是拉取操作的直接阻断点。Metric 数据中 `restart_count` 为 0 与 `waiting_reason` 为 `ImagePullBackOff` 进一步确认了容器尚未成功启动过且正在执行拉取逻辑的挂起状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod配置了无效的镜像仓库域名 (registry.invalid) → 集群DNS无法解析该域名 (no such host) → 镜像拉取失败 (ErrImagePull) → Pod 状态停滞在 Pending 且容器进入 ImagePullBackOff
```

### 根因结论

已确认根因为：**Pod 配置了无效的镜像仓库域名 `registry.invalid`，导致集群 DNS 无法解析该域名，从而引发镜像拉取失败。**

该结论由以下证据直接支撑：
1. K8s Event 明确指出 `lookup registry.invalid ... no such host`，证实网络/域名层面的不可达性（证据编号 4）。
2. K8s State 与 Metric 一致确认了 `ImagePullBackOff` 状态及 Pending 阶段，排除了调度或资源竞争等其他常见原因（证据编号 2, 3, 6）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 25.3s
├─ 并发证据采集: 41.5s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 41.5s (Evidence 37.3s, RCA 4.0s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
