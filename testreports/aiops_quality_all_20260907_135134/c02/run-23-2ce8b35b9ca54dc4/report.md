## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-nqrzv` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-nqrzv 处于 ImagePullBackOff 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Failed to pull image "registry.invalid/aiops/workload:missing": rpc error: ... failed to resolve reference ... failed to do request: Head "https://registry.invalid/v2/aiops/workload/manifests/missing": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 证明节点 DNS 解析失败，镜像拉取因网络不可达而终止 |
| 2 | K8s Event | kubelet | `Error: ImagePullBackOff` | 确认镜像拉取反复失败后的标准退避状态 |
| 3 | K8s State | kubelet | `container.waiting_reason`: `ImagePullBackOff` | 直接反映容器当前处于等待镜像拉取完成的阻塞状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 为 `1` (label: `ImagePullBackOff`) | 指标确认容器持续处于等待状态且无重启，符合网络/配置类故障特征 |
| 5 | K8s State | kubelet | `pod.status`: `Pending` | 确认 Pod 因容器无法启动而停留在挂起状态 |

**证据说明：**
1. 证据 1 中的 DNS 报错信息 (`no such host`) 为故障提供了唯一的确定性解释：目标镜像仓库域名 `registry.invalid` 在当前集群 DNS (`127.0.0.53`) 下不存在。
2. 证据 2、3、4 和 5 从不同维度一致地印证了容器无法启动（Waiting/Pending）的现象，其中 `restart_count=0`（未体现但隐含于状态）与 DNS 错误逻辑吻合（配置错误导致无法启动，故不会重启）。

## 🎯 根因分析 · g1

### 因果链

```text
镜像仓库域名 registry.invalid DNS 解析失败 (no such host) → 容器运行时 kubelet 无法建立 HTTP 连接拉取镜像 → 镜像拉取反复失败并进入退避状态 (ImagePullBackOff) → Pod 保持 Pending 状态无法运行
```

### 根因结论

已确认的根因是 **Pod 配置的镜像仓库域名 `registry.invalid` 无效**（可能为拼写错误、测试环境未配置本地 DNS 或 Hosts）。

该配置导致节点在执行 `ImagePull` 时，DNS 查询失败（`lookup registry.invalid ... no such host`），进而使容器运行时无法拉取镜像。这一网络层面的配置错误直接导致了 `ImagePullBackOff` 状态和 Pod 无法进入运行状态。

---

## 📊 性能统计

```text
├─ 总耗时: 59.8s
├─ 问题定位: 14.2s
├─ 并发证据采集: 36.6s
│  └─ g1 aiops-case-02/workload-65b7f54794-nqrzv: 36.6s (Evidence 28.3s, RCA 8.1s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-nqrzv**: pod-imagepull-failed
