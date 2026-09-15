## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod aiops-case-02/workload-65b7f54794-z7kdp 处于 ImagePullBackOff 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning  Failed ... Failed to pull image "registry.invalid/aiops/workload:missing": ... Head "https://registry.invalid/v2/aiops/workload/manifests/missing": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 直接证实 kubelet 访问镜像仓库时因 DNS 查询失败而中断 |
| 2 | K8s Event | kubelet | `Warning  Failed ... Error: ErrImagePull` | 证实镜像拉取动作失败 |
| 3 | K8s Event | kubelet | `Normal   BackOff ... Back-off pulling image "registry.invalid/aiops/workload:missing"` | 证实 kubelet 在拉取失败后进入退避重试状态 |
| 4 | K8s State | K8s | `Waiting Reason: ImagePullBackOff`, `Waiting Message: Back-off pulling image "registry.invalid/aiops/workload:missing"` | 证实容器长期处于拉取失败的退避等待阶段 |
| 5 | K8s State | K8s | `Pod Status: Pending`, `ContainersReady: False` | 证实 Pod 因容器未就绪卡在调度后阶段 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` | 从监控侧确认该 Pod 处于 ImagePullBackOff 状态 |

**证据关联与印证：**
K8s Event 中的 DNS 错误原文 `lookup registry.invalid on 127.0.0.53:53: no such host` 证实了底层网络解析层面的失败，这直接导致了 K8s State 中的 `ImagePullBackOff` 现象以及 Metric 中的状态确认。由于 Pod 处于 Pending 且未启动，Logging 和 Tracing 维度无物理数据，Kubernetes 内部状态和事件是唯一可观测的诊断依据。

## 🎯 根因分析 · g1

### 因果链

```text
DNS 解析失败 (lookup registry.invalid ... no such host) → 镜像拉取失败 (ErrImagePull) → Kubelet 退避重试 (ImagePullBackOff) → Pod 状态维持在 Pending
```

### 根因结论

**已确认的根因：**
镜像仓库 `registry.invalid` 的域名解析失败（DNS 报错 `no such host`）。
由于无法解析该域名，kubelet 无法与镜像仓库建立连接以拉取 `registry.invalid/aiops/workload:missing` 镜像，进而触发 K8s 的 `ImagePullBackOff` 机制，导致 Pod `aiops-case-02/workload-65b7f549794-z7kdp` 始终无法启动并保持 `Pending` 状态。

**不确定性说明：**
证据表明是 DNS 查询失败（指向 127.0.0.53:53），但未能确定这是集群全局的 DNS 服务故障，还是该特定域名 `registry.invalid` 仅在当前节点（或该集群）的网络配置中未定义。未排查 Node2 节点的 `/etc/resolv.conf` 配置细节，也无法确认是否有其他域名同样受阻。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 20.5s
├─ 并发证据采集: 64.2s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 64.2s (Evidence 55.8s, RCA 8.3s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
