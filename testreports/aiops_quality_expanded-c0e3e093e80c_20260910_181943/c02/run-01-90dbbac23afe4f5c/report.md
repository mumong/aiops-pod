## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-02/workload-65b7f54794-z7kdp` | ImagePullBackOff | Pod workload-65b7f54794-z7kdp 处于 ImagePullBackOff 状态，镜像拉取失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning Failed ... Failed to pull image "registry.invalid/aiops/workload:missing": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | 记录根本原因：DNS 解析失败导致无法连接镜像仓库。 |
| 2 | K8s Event | kubelet | `Normal BackOff ... Back-off pulling image "registry.invalid/aiops/workload:missing"` | 记录直接现象：因拉取失败进入退避状态。 |
| 3 | K8s Config | Kubernetes | `container.image: "registry.invalid/aiops/workload:missing"` | 确认 Pod 配置了无效的镜像域名。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ImagePullBackOff"} = 1` | 观测确认容器处于 ImagePullBackOff 等待状态。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 0` | 排除容器启动后异常退出的可能性。 |

**证据关联说明**
Kubernetes 事件（#1）提供的错误原文直接证实了网络连通性失败的具体原因（DNS 解析 `no such host`），这排除了凭证错误或网络策略拦截等其它可能性。事件（#2）描述的 BackOff 状态与 Metric（#4）的 `ImagePullBackOff` 信号一致，同时重启计数为 0（#5）佐证了容器始终未能通过 `ErrImagePull` 阶段，未发生过任何有效启动。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了无效的镜像仓库域名 registry.invalid → 集群 DNS (127.0.0.53) 无法解析该主机名 (no such host) → kubelet 发起的拉取请求失败 (ErrImagePull) → Pod 持续处于退避重试状态 (ImagePullBackOff)
```

### 根因结论

**已确认的根因**：Pod 配置了不可达的镜像仓库域名 `registry.invalid`，导致集群 DNS 解析失败。
**证据引用**：
1. **事件层面**：Kubelet 上报了明确的 `dial tcp: lookup registry.invalid ... no such host` 错误（#1），确认连接建立前的 DNS 阶段即已失败。
2. **状态层面**：Pod 处于 `Pending` 且处于 `ImagePullBackOff` 状态（#2, #4），且重启次数始终为 0（#5），确认容器进程从未启动，符合镜像拉取失败的典型特征。
3. **配置层面**：Pod 显式配置了该无效域名（#3）。
综合以上事实，判定为镜像配置错误导致的拉取失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 16.7s
├─ 并发证据采集: 46.7s
│  └─ g1 aiops-case-02/workload-65b7f54794-z7kdp: 46.7s (Evidence 38.4s, RCA 8.2s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-02/workload-65b7f54794-z7kdp**: pod-imagepull-failed
