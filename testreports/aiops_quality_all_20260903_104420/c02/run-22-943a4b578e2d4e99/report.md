## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-rnlv4` | ImagePullBackOff | Pod workload-65b7f54794-rnlv4 处于 ImagePullBackOff 状态，容器 app 无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Error: ImagePullBackOff` 及 `Failed to pull image "registry.invalid/aiops/workload:missing"` (fact-05513ae6377d, fact-fd398c30a224) | 直接证明 Pod 处于拉取镜像失败后的退避状态。 |
| 2 | K8s Event | kubernetes | `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (fact-0caad4edcff4, fact-596a52590dbd) | 根因定位证据：显示底层网络因 DNS 解析失败导致连接拒绝。 |
| 3 | K8s State | kubernetes | `pod.status: Pending` (fact-11891fe12e74) | 佐证 Pod 未进入运行态。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1, reason=`ImagePullBackOff` (fact-be64ee662e4e) | 独立于 K8s 事件指标，从集群状态层面印证 Pod 正在等待且原因为镜像拉取失败。 |

**证据关联：**
Kubernetes 事件 `fact-0caad4edcff4` 中的详细错误明确将镜像地址 `registry.invalid/aiops/workload:missing` 与 `no such host` DNS 解析失败建立因果联系；Metric `fact-be64ee662e4e` 在宏观状态层面复现了该等待原因，排除了偶发性网络抖动的可能，确认为持续的配置错误导致的阻塞。

## 🎯 根因分析 · g1

### 因果链

```text
Deployment 配置了无效的镜像仓库域名 registry.invalid → 集群 DNS 解析失败 (no such host) → kubelet 拉取镜像遭遇网络拒绝 (ErrImagePull) → 容器进入 ImagePullBackOff 状态
```

### 根因结论

已确认根因为 **镜像仓库域名配置错误 (`registry.invalid`)**。
真实事实 `fact-0caad4edcff4` 中的 `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` 直接揭示了 DNS 层面无此主机的解析失败，导致 kubelet 无法建立 TCP 连接并拉取 `registry.invalid/aiops/workload:missing` 镜像，进而触发 `ImagePullBackOff` 状态并持续退避重试。证据完整，逻辑闭环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 19.7s
├─ 并发证据采集: 62.0s
│  └─ g1 aiops-case-02/workload-65b7f54794-rnlv4: 62.0s (Evidence 51.8s, RCA 10.1s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-rnlv4**: pod-imagepull-failed
